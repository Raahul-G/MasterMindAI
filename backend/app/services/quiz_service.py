import logging
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning import Answer, Module, Passage, Question, Quiz, Remediation, TopicNode
from app.models.user import User
from app.schemas.learning import AnswerSubmission
from app.services import achievement_service, feed_service, notion_service, recommendation_service, streak_service

logger = logging.getLogger(__name__)


async def score_quiz(
    quiz_id: uuid.UUID,
    answer_submissions: list[AnswerSubmission],
    db: AsyncSession,
    local_date: date | None = None,
) -> dict:
    """
    Scores a quiz by comparing user answers to correct answers.
    Saves all answers to the database.
    If the quiz is fully passed, marks the module completed and triggers
    streak + achievement updates automatically.
    Returns score, total, passed flag, and list of failed concept titles.
    """
    result = await db.execute(select(Question).where(Question.quiz_id == quiz_id))
    questions = result.scalars().all()
    questions_by_id = {q.id: q for q in questions}

    correct_count = 0
    failed_passage_ids = set()

    for submission in answer_submissions:
        question = questions_by_id.get(submission.question_id)
        if not question:
            continue

        is_correct = submission.user_answer.strip() == question.correct_answer.strip()
        if is_correct:
            correct_count += 1
        else:
            failed_passage_ids.add(question.passage_id)

        db.add(Answer(
            quiz_id=quiz_id,
            question_id=submission.question_id,
            user_answer=submission.user_answer,
            is_correct=is_correct,
        ))

    total = len(answer_submissions)
    passed = correct_count == total

    # Variables saved before commit — SQLAlchemy expires objects after db.commit()
    completing_user_id = None
    completing_module_id = None
    completing_topic = None
    completing_level = None
    completing_score = correct_count
    completing_total = total
    completing_concept_titles: list[str] = []
    completing_canonical: str | None = None
    completing_domain: str | None = None
    is_first_attempt_perfect = False

    quiz_result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = quiz_result.scalar_one_or_none()
    if quiz:
        quiz.score = correct_count
        quiz.total_questions = total
        quiz.passed = passed
        quiz.submitted_at = datetime.now(timezone.utc)

        if passed:
            module_result = await db.execute(
                select(Module).where(Module.id == quiz.module_id)
            )
            module = module_result.scalar_one_or_none()
            if module and module.status != "completed":
                module.status = "completed"
                module.completed_at = datetime.now(timezone.utc)
                completing_user_id = module.user_id
                completing_module_id = module.id
                completing_topic = module.topic
                completing_level = module.level
                is_first_attempt_perfect = quiz.attempt_number == 1

                # Fetch concept titles before commit (objects expire after commit)
                passage_result = await db.execute(
                    select(Passage).where(Passage.module_id == module.id).order_by(Passage.order_index)
                )
                completing_concept_titles = [p.concept_title for p in passage_result.scalars().all()]

                # Fetch canonical_name from topic_nodes before commit
                node_result = await db.execute(
                    select(TopicNode).where(TopicNode.source_module_id == module.id)
                )
                completing_node = node_result.scalar_one_or_none()
                completing_canonical = completing_node.canonical_name if completing_node else completing_topic
                completing_domain = completing_node.domain if completing_node else None

    await db.commit()

    # Trigger streak + achievement + Notion updates for a newly completed module
    notion_page_url: str | None = None

    if completing_user_id:
        streak = await streak_service.update_streak(completing_user_id, db, local_date)

        remediation_result = await db.execute(
            select(func.count()).select_from(Remediation)
            .where(Remediation.module_id == completing_module_id)
        )
        used_remediation = (remediation_result.scalar() or 0) > 0

        await achievement_service.check_and_award_achievements(
            user_id=completing_user_id,
            db=db,
            streak_count=streak.current_streak,
            used_remediation=used_remediation,
            first_attempt_perfect=is_first_attempt_perfect,
        )

        await feed_service.post_activity(
            user_id=completing_user_id,
            activity_type="module_completed",
            metadata={
                "topic": completing_topic,
                "level": completing_level,
                "score": completing_score,
                "total": completing_total,
            },
            db=db,
        )

        # Auto-create Notion sub-page if the user has Notion connected
        user_result = await db.execute(select(User).where(User.id == completing_user_id))
        user = user_result.scalar_one_or_none()
        if (
            user
            and user.notion_access_token
            and user.notion_mastermind_page_id
            and completing_module_id
        ):
            try:
                notion_page_url = await notion_service.create_module_subpage(
                    access_token=user.notion_access_token,
                    mastermind_page_id=user.notion_mastermind_page_id,
                    module_id=completing_module_id,
                    db=db,
                )
                # Save the Notion page URL back to the module
                module_update = await db.execute(
                    select(Module).where(Module.id == completing_module_id)
                )
                completed_module = module_update.scalar_one_or_none()
                if completed_module:
                    completed_module.notion_page_id = notion_page_url.split("/")[-1]
                    await db.commit()
            except Exception as exc:
                logger.warning("Notion auto-export failed for module %s: %s", completing_module_id, exc)

        # Update topic node status to learned and generate recommendations
        try:
            await recommendation_service.complete_topic_node(
                completing_user_id, completing_canonical or completing_topic, db
            )
            await recommendation_service.generate_and_save_recommendations(
                user_id=completing_user_id,
                source_module_id=completing_module_id,
                topic=completing_topic,
                canonical_name=completing_canonical or completing_topic,
                domain=completing_domain,
                level=completing_level,
                learned_concepts=completing_concept_titles,
                user_interests=user.interest_topics or [] if user else [],
                db=db,
            )
        except Exception as exc:
            logger.warning("Recommendation generation failed for module %s: %s", completing_module_id, exc)

    # Fetch failed concept titles from the passages
    failed_concepts = []
    if failed_passage_ids:
        passage_result = await db.execute(
            select(Passage).where(Passage.id.in_(failed_passage_ids))
        )
        failed_passages = passage_result.scalars().all()
        failed_concepts = [p.concept_title for p in failed_passages]

    return {
        "score": correct_count,
        "total": total,
        "passed": passed,
        "failed_concepts": failed_concepts,
        "notion_page_url": notion_page_url,
    }
