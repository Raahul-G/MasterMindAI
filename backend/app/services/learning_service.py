import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning import Module, Passage, Question, Quiz, Remediation
from app.models.user import User
from app.schemas.learning import (
    GenerateQuizResponse,
    PassageResponse,
    QuestionResponse,
    RemediateResponse,
    RemediationResponse,
    StartModuleResponse,
)
from app.services import ai_service, recommendation_service


async def start_module(
    topic: str,
    level: str,
    user: User,
    db: AsyncSession,
    prerequisite_concepts: list[str] | None = None,
) -> StartModuleResponse:
    """
    Starts a new learning module:
    1. Generates ELI5 using the user's stored interests
    2. Generates 2-3 passages at the chosen level (graph-aware if prerequisites provided)
    3. Saves everything to the database
    4. Returns the module ID, ELI5, and passages
    """
    interests = user.interest_topics or ["general knowledge", "science", "history"]

    eli5_text = await ai_service.generate_eli5(topic, level, interests)
    raw_passages = await ai_service.generate_passages(
        topic, level, eli5_text, prerequisite_concepts=prerequisite_concepts
    )

    module = Module(user_id=user.id, topic=topic, level=level, eli5_text=eli5_text)
    db.add(module)
    await db.flush()

    passages = []
    for i, p in enumerate(raw_passages):
        passage = Passage(
            module_id=module.id,
            concept_title=p["concept_title"],
            content=p["content"],
            order_index=i + 1,
        )
        db.add(passage)
        passages.append(passage)

    await db.commit()
    for p in passages:
        await db.refresh(p)
    await db.refresh(module)

    # Normalise topic and create in_progress node (fire-and-forget, non-blocking)
    try:
        await recommendation_service.create_or_update_topic_node(
            user_id=user.id,
            topic=topic,
            module_id=module.id,
            status="in_progress",
            db=db,
        )
    except Exception:
        pass

    return StartModuleResponse(
        module_id=module.id,
        eli5_text=eli5_text,
        passages=[PassageResponse.model_validate(p) for p in passages],
    )


async def generate_quiz_for_module(
    module_id: uuid.UUID,
    db: AsyncSession,
) -> GenerateQuizResponse:
    """
    Generates a quiz for an existing module:
    1. Fetches the module's passages from the database
    2. Calls Claude to generate questions based on those passages
    3. Saves all questions to the database
    4. Returns the quiz ID and questions (without correct answers)
    """
    passage_result = await db.execute(
        select(Passage).where(Passage.module_id == module_id).order_by(Passage.order_index)
    )
    passages = passage_result.scalars().all()

    module_result = await db.execute(select(Module).where(Module.id == module_id))
    module = module_result.scalar_one()

    passages_content = [{"concept_title": p.concept_title, "content": p.content} for p in passages]
    raw_questions = await ai_service.generate_quiz(module.topic, passages_content, module.level)

    existing_result = await db.execute(select(Quiz).where(Quiz.module_id == module_id))
    attempt_number = len(existing_result.scalars().all()) + 1

    quiz = Quiz(module_id=module_id, attempt_number=attempt_number)
    db.add(quiz)
    await db.flush()

    passage_map = {p.concept_title: p.id for p in passages}
    questions = []
    for i, q in enumerate(raw_questions):
        passage_id = passage_map.get(q["concept_title"], passages[0].id)
        question = Question(
            quiz_id=quiz.id,
            passage_id=passage_id,
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

    passage_id_to_title = {p.id: p.concept_title for p in passages}

    return GenerateQuizResponse(
        quiz_id=quiz.id,
        questions=[
            QuestionResponse(
                id=q.id,
                concept_title=passage_id_to_title.get(q.passage_id, ""),
                question_text=q.question_text,
                question_type=q.question_type,
                options=q.options or [],
                order_index=q.order_index,
            )
            for q in questions
        ],
    )


async def remediate(
    module_id: uuid.UUID,
    quiz_id: uuid.UUID,
    failed_concepts: list[str],
    db: AsyncSession,
) -> RemediateResponse:
    """
    Generates fresh remediation explanations for failed concepts:
    1. Fetches the original passages for context
    2. Calls Claude to generate new explanations using different analogies
    3. Saves remediations to the database
    4. Returns the new explanations
    """
    module_result = await db.execute(select(Module).where(Module.id == module_id))
    module = module_result.scalar_one()

    passage_result = await db.execute(select(Passage).where(Passage.module_id == module_id))
    passages = passage_result.scalars().all()
    original_passages = [{"concept_title": p.concept_title, "content": p.content} for p in passages]

    raw_remediations = await ai_service.generate_remediation(
        module.topic, failed_concepts, original_passages
    )

    passage_map = {p.concept_title: p.id for p in passages}
    for r in raw_remediations:
        passage_id = passage_map.get(r["concept_title"], passages[0].id)
        db.add(Remediation(
            module_id=module_id,
            passage_id=passage_id,
            quiz_id=quiz_id,
            content=r["content"],
        ))

    await db.commit()

    return RemediateResponse(
        remediations=[RemediationResponse(**r) for r in raw_remediations]
    )
