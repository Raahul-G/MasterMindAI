import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning import Answer, Passage, Question, Quiz
from app.schemas.learning import AnswerSubmission


async def score_quiz(
    quiz_id: uuid.UUID,
    answer_submissions: list[AnswerSubmission],
    db: AsyncSession,
) -> dict:
    """
    Scores a quiz by comparing user answers to correct answers.
    Saves all answers to the database.
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

    # Update quiz record with results
    quiz_result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = quiz_result.scalar_one_or_none()
    if quiz:
        quiz.score = correct_count
        quiz.total_questions = total
        quiz.passed = passed
        quiz.submitted_at = datetime.now(timezone.utc)

    await db.commit()

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
    }
