import logging
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning import Answer, Module, Passage, Question, Quiz
from app.models.user import User
from app.schemas.learning import AnswerSubmission, PassageResponse, QuestionResponse
from app.services import achievement_service, ai_service, feed_service, graph_service, notion_service, streak_service

logger = logging.getLogger(__name__)


async def _count_concepts_learned(module_id: uuid.UUID, db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count()).select_from(Passage)
        .where(Passage.module_id == module_id, Passage.status == "completed")
    )
    return result.scalar() or 0


async def _create_quiz_inline(
    passage: Passage,
    module: Module,
    db: AsyncSession,
) -> tuple[Quiz, list[Question]]:
    """Creates a quiz for the given passage inline (no external service import needed)."""
    passages_content = [{
        "concept_title": passage.concept_title,
        "summary": passage.summary,
        "content": passage.content,
        "use_cases": passage.use_cases,
    }]
    raw_questions = await ai_service.generate_quiz(module.topic, passages_content, module.level)

    existing_result = await db.execute(
        select(func.count()).select_from(Quiz).where(Quiz.passage_id == passage.id)
    )
    attempt_number = (existing_result.scalar() or 0) + 1

    quiz = Quiz(module_id=module.id, passage_id=passage.id, attempt_number=attempt_number)
    db.add(quiz)
    await db.flush()

    questions = []
    for i, q in enumerate(raw_questions):
        question = Question(
            quiz_id=quiz.id,
            passage_id=passage.id,
            question_text=q["question_text"],
            question_type=q["question_type"],
            options=q["options"],
            correct_answer=q["correct_answer"],
            order_index=i + 1,
        )
        db.add(question)
        questions.append(question)

    await db.commit()
    for q in questions:
        await db.refresh(q)
    await db.refresh(quiz)

    return quiz, questions


async def score_quiz(
    quiz_id: uuid.UUID,
    answer_submissions: list[AnswerSubmission],
    db: AsyncSession,
    local_date: date | None = None,
) -> dict:
    """
    Scores a per-passage quiz.
    On pass: marks the passage completed, fires streak/achievements,
    and returns the next passage (if within the same pair) or needs_new_pair=True.
    On fail: returns failed concepts for remediation.
    """
    result = await db.execute(select(Question).where(Question.quiz_id == quiz_id))
    questions = result.scalars().all()
    questions_by_id = {q.id: q for q in questions}

    correct_count = 0
    failed_passage_ids: set[uuid.UUID] = set()

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

    quiz_result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = quiz_result.scalar_one_or_none()
    if quiz:
        quiz.score = correct_count
        quiz.total_questions = total
        quiz.passed = passed
        quiz.submitted_at = datetime.now(timezone.utc)

    await db.commit()

    if not passed:
        failed_concepts = []
        if failed_passage_ids:
            passage_result = await db.execute(
                select(Passage).where(Passage.id.in_(failed_passage_ids))
            )
            failed_concepts = [p.concept_title for p in passage_result.scalars().all()]

        concepts_learned = await _count_concepts_learned(quiz.module_id, db) if quiz else 0
        return {
            "score": correct_count,
            "total": total,
            "passed": False,
            "failed_concepts": failed_concepts,
            "next_passage": None,
            "next_quiz_id": None,
            "next_questions": [],
            "needs_new_pair": False,
            "concepts_learned": concepts_learned,
        }

    # --- Passed ---
    # 1. Mark the passage completed
    current_passage: Passage | None = None
    module: Module | None = None

    if quiz and quiz.passage_id:
        passage_result = await db.execute(select(Passage).where(Passage.id == quiz.passage_id))
        current_passage = passage_result.scalar_one_or_none()
        if current_passage:
            current_passage.status = "completed"

        module_result = await db.execute(select(Module).where(Module.id == quiz.module_id))
        module = module_result.scalar_one_or_none()

        await db.commit()

    concepts_learned = await _count_concepts_learned(quiz.module_id, db) if quiz else 0

    # 2. Fire streak + achievements on concept completion
    # Snapshot PKs before the try block — if rollback() is called, SQLAlchemy expires all
    # loaded ORM objects. Accessing their attributes in async context then raises
    # "greenlet_spawn has not been called" (async lazy-load not supported).
    _passage_id = current_passage.id if current_passage else None
    _module_id = module.id if module else None

    if quiz and module:
        try:
            streak = await streak_service.update_streak(module.user_id, db, local_date)

            # Total completed passages across ALL of this user's modules
            total_concepts_result = await db.execute(
                select(func.count(Passage.id))
                .join(Module, Passage.module_id == Module.id)
                .where(Module.user_id == module.user_id, Passage.status == "completed")
            )
            total_concepts = total_concepts_result.scalar() or 0

            await achievement_service.check_and_award_achievements(
                user_id=module.user_id,
                db=db,
                streak_count=streak.current_streak,
                total_concepts=total_concepts,
            )

            await feed_service.post_activity(
                user_id=module.user_id,
                activity_type="module_completed",
                metadata={
                    "topic": module.topic,
                    "level": module.level,
                    "concept": current_passage.concept_title if current_passage else "",
                },
                db=db,
            )

            await notion_service.sync_concept_to_notion(
                user_id=module.user_id,
                module_id=module.id,
                passage_id=current_passage.id,
                quiz_id=quiz_id,
                db=db,
            )

            if current_passage:
                await graph_service.embed_and_upsert(
                    user_id=module.user_id,
                    concept_title=current_passage.concept_title,
                    content=current_passage.content,
                    module_id=module.id,
                    db=db,
                )
        except Exception as exc:
            logger.warning("Post-completion side-effects failed for quiz %s: %s", quiz_id, exc)
            await db.rollback()
            # Re-fetch ORM objects that were expired by rollback, so the "find next passage"
            # step below can access their attributes without triggering async lazy-load errors.
            if _passage_id:
                r = await db.execute(select(Passage).where(Passage.id == _passage_id))
                current_passage = r.scalar_one_or_none()
            if _module_id:
                r = await db.execute(select(Module).where(Module.id == _module_id))
                module = r.scalar_one_or_none()

    # 3. Look for next passage in same module (order_index + 1)
    next_passage: Passage | None = None
    next_quiz: Quiz | None = None
    next_questions: list[Question] = []
    needs_new_pair = False

    if current_passage and module:
        next_result = await db.execute(
            select(Passage).where(
                Passage.module_id == current_passage.module_id,
                Passage.order_index == current_passage.order_index + 1,
            )
        )
        next_passage = next_result.scalar_one_or_none()

        if next_passage:
            # Next passage already in DB (within same pair) — auto-create its quiz
            try:
                next_quiz, next_questions = await _create_quiz_inline(next_passage, module, db)
            except Exception as exc:
                logger.warning("Failed to create quiz for next passage %s: %s", next_passage.id, exc)
                next_passage = None
        else:
            needs_new_pair = True

    return {
        "score": correct_count,
        "total": total,
        "passed": True,
        "failed_concepts": [],
        "next_passage": PassageResponse.model_validate(next_passage) if next_passage else None,
        "next_quiz_id": next_quiz.id if next_quiz else None,
        "next_questions": [
            QuestionResponse(
                id=q.id,
                concept_title=next_passage.concept_title if next_passage else "",
                question_text=q.question_text,
                question_type=q.question_type,
                options=q.options or [],
                order_index=q.order_index,
            )
            for q in next_questions
        ],
        "needs_new_pair": needs_new_pair,
        "concepts_learned": concepts_learned,
    }
