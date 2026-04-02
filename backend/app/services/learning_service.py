import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException
from app.models.learning import Module, Passage, Question, Quiz, Remediation
from app.models.user import User
from app.schemas.learning import (
    GenerateQuizResponse,
    NextPairResponse,
    PassageResponse,
    QuestionResponse,
    RemediateResponse,
    RemediationResponse,
    StartModuleResponse,
)
from app.services import ai_service


async def _count_concepts_learned(module_id: uuid.UUID, db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count()).select_from(Passage)
        .where(Passage.module_id == module_id, Passage.status == "completed")
    )
    return result.scalar() or 0


async def _create_quiz_for_passage(
    passage: Passage,
    module: Module,
    db: AsyncSession,
) -> tuple[Quiz, list[Question]]:
    """Creates a quiz (and questions) for a single passage. Returns the quiz + questions."""
    passages_content = [{
        "concept_title": passage.concept_title,
        "summary": passage.summary,
        "content": passage.content,
        "use_cases": passage.use_cases,
    }]
    raw_questions = await ai_service.generate_quiz(module.topic, passages_content, module.level)

    # attempt_number = how many quizzes already exist for this passage + 1
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
    2. Generates the first pair of passages (exactly 2)
    3. Creates a quiz for passage 1
    4. Returns module ID, ELI5, passage 1, and its quiz questions
    """
    interests = user.interest_topics or ["general knowledge", "science", "history"]

    eli5_text = await ai_service.generate_eli5(topic, level, interests)
    raw_passages = await ai_service.generate_passages(
        topic, level, eli5_text,
        prerequisite_concepts=prerequisite_concepts,
        covered_concepts=[],
    )

    module = Module(user_id=user.id, topic=topic, level=level, eli5_text=eli5_text)
    db.add(module)
    await db.flush()

    passages = []
    for i, p in enumerate(raw_passages):
        passage = Passage(
            module_id=module.id,
            concept_title=p["concept_title"],
            summary=p.get("summary"),
            content=p["content"],
            use_cases=p.get("use_cases"),
            order_index=i + 1,
            status="in_progress",
        )
        db.add(passage)
        passages.append(passage)

    await db.commit()
    for p in passages:
        await db.refresh(p)
    await db.refresh(module)

    # Generate quiz for the first passage only
    first_passage = passages[0]
    quiz, questions = await _create_quiz_for_passage(first_passage, module, db)

    return StartModuleResponse(
        module_id=module.id,
        eli5_text=eli5_text,
        current_passage=PassageResponse.model_validate(first_passage),
        quiz_id=quiz.id,
        questions=[
            QuestionResponse(
                id=q.id,
                concept_title=first_passage.concept_title,
                question_text=q.question_text,
                question_type=q.question_type,
                options=q.options or [],
                order_index=q.order_index,
            )
            for q in questions
        ],
        concepts_learned=0,
    )


async def generate_quiz_for_passage(
    passage_id: uuid.UUID,
    db: AsyncSession,
) -> GenerateQuizResponse:
    """Generates a fresh quiz for a single passage (used for retry after remediation)."""
    passage_result = await db.execute(select(Passage).where(Passage.id == passage_id))
    passage = passage_result.scalar_one_or_none()
    if not passage:
        raise HTTPException(status_code=404, detail="Passage not found")

    module_result = await db.execute(select(Module).where(Module.id == passage.module_id))
    module = module_result.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    quiz, questions = await _create_quiz_for_passage(passage, module, db)

    return GenerateQuizResponse(
        quiz_id=quiz.id,
        questions=[
            QuestionResponse(
                id=q.id,
                concept_title=passage.concept_title,
                question_text=q.question_text,
                question_type=q.question_type,
                options=q.options or [],
                order_index=q.order_index,
            )
            for q in questions
        ],
    )


async def generate_next_pair(
    module_id: uuid.UUID,
    covered_concepts: list[str] | None,
    db: AsyncSession,
) -> NextPairResponse:
    """
    Generates the next pair of passages for a module.
    Called when the user clicks "Continue" after completing a pair.
    Returns the first passage of the new pair with its quiz.
    """
    module_result = await db.execute(select(Module).where(Module.id == module_id))
    module = module_result.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    # Get current highest order_index to continue from
    max_result = await db.execute(
        select(func.max(Passage.order_index)).where(Passage.module_id == module_id)
    )
    max_index = max_result.scalar() or 0

    # Fetch all completed concept titles from DB — don't rely on frontend list
    completed_result = await db.execute(
        select(Passage)
        .where(Passage.module_id == module_id, Passage.status == "completed")
        .order_by(Passage.order_index)
    )
    db_covered = [p.concept_title for p in completed_result.scalars().all()]
    effective_covered = db_covered if db_covered else (covered_concepts or [])

    raw_passages = await ai_service.generate_passages(
        module.topic,
        module.level,
        module.eli5_text,
        covered_concepts=effective_covered,
    )

    new_passages = []
    for i, p in enumerate(raw_passages):
        passage = Passage(
            module_id=module_id,
            concept_title=p["concept_title"],
            summary=p.get("summary"),
            content=p["content"],
            use_cases=p.get("use_cases"),
            order_index=max_index + i + 1,
            status="in_progress",
        )
        db.add(passage)
        new_passages.append(passage)

    await db.commit()
    for p in new_passages:
        await db.refresh(p)

    first_passage = new_passages[0]
    quiz, questions = await _create_quiz_for_passage(first_passage, module, db)
    concepts_learned = await _count_concepts_learned(module_id, db)

    return NextPairResponse(
        current_passage=PassageResponse.model_validate(first_passage),
        quiz_id=quiz.id,
        questions=[
            QuestionResponse(
                id=q.id,
                concept_title=first_passage.concept_title,
                question_text=q.question_text,
                question_type=q.question_type,
                options=q.options or [],
                order_index=q.order_index,
            )
            for q in questions
        ],
        concepts_learned=concepts_learned,
    )


async def resume_module(
    module_id: uuid.UUID,
    db: AsyncSession,
) -> StartModuleResponse:
    """
    Resumes an existing module by finding the first in-progress passage
    and generating a fresh quiz for it.
    """
    module_result = await db.execute(select(Module).where(Module.id == module_id))
    module = module_result.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    # Find first in-progress passage, fallback to the last passage
    passage_result = await db.execute(
        select(Passage)
        .where(Passage.module_id == module_id, Passage.status == "in_progress")
        .order_by(Passage.order_index)
    )
    passage = passage_result.scalars().first()

    if not passage:
        # All completed — generate a fresh pair instead of replaying old content
        completed_result = await db.execute(
            select(Passage)
            .where(Passage.module_id == module_id)
            .order_by(Passage.order_index)
        )
        all_passages = completed_result.scalars().all()
        if not all_passages:
            raise HTTPException(status_code=404, detail="No passages found for this module")
        covered = [p.concept_title for p in all_passages]
        next_pair = await generate_next_pair(module_id, covered, db)
        return StartModuleResponse(
            module_id=module.id,
            eli5_text=module.eli5_text,
            current_passage=next_pair.current_passage,
            quiz_id=next_pair.quiz_id,
            questions=next_pair.questions,
            concepts_learned=next_pair.concepts_learned,
        )

    if not passage:
        raise HTTPException(status_code=404, detail="No passages found for this module")

    quiz, questions = await _create_quiz_for_passage(passage, module, db)
    concepts_learned = await _count_concepts_learned(module_id, db)

    return StartModuleResponse(
        module_id=module.id,
        eli5_text=module.eli5_text,
        current_passage=PassageResponse.model_validate(passage),
        quiz_id=quiz.id,
        questions=[
            QuestionResponse(
                id=q.id,
                concept_title=passage.concept_title,
                question_text=q.question_text,
                question_type=q.question_type,
                options=q.options or [],
                order_index=q.order_index,
            )
            for q in questions
        ],
        concepts_learned=concepts_learned,
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
    module = module_result.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

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
