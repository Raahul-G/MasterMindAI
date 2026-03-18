import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning import Answer, Module, Passage, Question, Quiz, Remediation


async def generate_module_markdown(module_id: uuid.UUID, db: AsyncSession) -> str:
    """
    Compiles a completed module into a Markdown summary string.
    Structure: title → ELI5 → Passages → Quiz Q&A → Remediations
    """
    module_result = await db.execute(select(Module).where(Module.id == module_id))
    module = module_result.scalar_one()

    passage_result = await db.execute(
        select(Passage).where(Passage.module_id == module_id).order_by(Passage.order_index)
    )
    passages = passage_result.scalars().all()

    # Fetch the most recent passed quiz
    quiz_result = await db.execute(
        select(Quiz)
        .where(Quiz.module_id == module_id, Quiz.passed == True)  # noqa: E712
        .order_by(Quiz.attempt_number.desc())
    )
    quiz = quiz_result.scalars().first()

    lines = []

    # Title block
    lines.append(f"# {module.topic}")
    lines.append(f"\n**Level:** {module.level.capitalize()}")
    if module.completed_at:
        lines.append(f"**Completed:** {module.completed_at.strftime('%Y-%m-%d')}")
    lines.append("\n---\n")

    # ELI5
    lines.append("## The Simple Version")
    lines.append(f"\n{module.eli5_text}\n")
    lines.append("\n---\n")

    # Passages
    lines.append("## Core Concepts")
    for passage in passages:
        lines.append(f"\n### {passage.concept_title}")
        lines.append(f"\n{passage.content}\n")
    lines.append("\n---\n")

    # Quiz Q&A
    if quiz:
        lines.append("## Quiz Results")
        lines.append(
            f"\n**Score:** {quiz.score}/{quiz.total_questions} — "
            f"{'Passed' if quiz.passed else 'Failed'}"
        )
        lines.append(f"**Attempts needed:** {quiz.attempt_number}\n")

        question_result = await db.execute(
            select(Question).where(Question.quiz_id == quiz.id).order_by(Question.order_index)
        )
        questions = question_result.scalars().all()

        answer_result = await db.execute(
            select(Answer).where(Answer.quiz_id == quiz.id)
        )
        answers = answer_result.scalars().all()
        answer_map = {a.question_id: a for a in answers}

        for i, q in enumerate(questions, 1):
            answer = answer_map.get(q.id)
            marker = "✓" if (answer and answer.is_correct) else "✗"
            lines.append(f"\n**Q{i}: {q.question_text}**")
            lines.append(f"Correct answer: {q.correct_answer}")
            if answer:
                lines.append(f"Your answer: {answer.user_answer} {marker}")

        lines.append("\n---\n")

    # Remediations
    remediation_result = await db.execute(
        select(Remediation).where(Remediation.module_id == module_id)
    )
    remediations = remediation_result.scalars().all()

    if remediations:
        lines.append("## Extra Help")
        passage_map = {p.id: p for p in passages}
        seen_passage_ids: set = set()

        for r in remediations:
            if r.passage_id not in seen_passage_ids:
                seen_passage_ids.add(r.passage_id)
                passage = passage_map.get(r.passage_id)
                title = passage.concept_title if passage else "Concept"
                lines.append(f"\n### {title} (revisited)")
            lines.append(f"\n{r.content}\n")

    return "\n".join(lines)
