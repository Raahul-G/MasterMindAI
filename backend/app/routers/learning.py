from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.learning import ConceptGraph, Module, Passage
from app.models.user import User
from app.schemas.learning import (
    ConceptNode,
    GenerateQuizRequest,
    GenerateQuizResponse,
    KnowledgeMapResponse,
    KnowledgeMapTopic,
    RemediateRequest,
    RemediateResponse,
    StartModuleRequest,
    StartModuleResponse,
    SubmitQuizRequest,
    SubmitQuizResponse,
)
from app.services import learning_service, quiz_service

router = APIRouter(prefix="/learn", tags=["learning"])


@router.post("/start", response_model=StartModuleResponse)
async def start_module(
    data: StartModuleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if data.level not in ("kid", "intermediate", "expert"):
        raise HTTPException(status_code=400, detail="Level must be kid, intermediate, or expert")
    return await learning_service.start_module(
        data.topic, data.level, current_user, db, prerequisite_concepts=data.prerequisite_concepts or None
    )


@router.get("/knowledge-map", response_model=KnowledgeMapResponse)
async def get_knowledge_map(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Fetch all completed modules for this user
    modules_result = await db.execute(
        select(Module).where(Module.user_id == current_user.id, Module.status == "completed")
    )
    completed_modules = modules_result.scalars().all()

    # Build module_id → topic map
    module_map = {m.id: m.topic for m in completed_modules}

    # Fetch all passages for completed modules
    if completed_modules:
        module_ids = [m.id for m in completed_modules]
        passages_result = await db.execute(
            select(Passage).where(Passage.module_id.in_(module_ids))
        )
        passages = passages_result.scalars().all()
    else:
        passages = []

    # Group learned concepts by topic
    topic_learned: dict[str, list[ConceptNode]] = defaultdict(list)
    for p in passages:
        topic = module_map.get(p.module_id, "Unknown")
        topic_learned[topic].append(ConceptNode(
            concept=p.concept_title,
            status="learned",
            module_id=str(p.module_id),
        ))

    # Fetch all concept graph entries for this user
    graph_result = await db.execute(
        select(ConceptGraph).where(ConceptGraph.user_id == current_user.id)
    )
    graph_entries = graph_result.scalars().all()

    # Collect all learned concept titles per topic (for deduplication)
    learned_titles_by_topic: dict[str, set[str]] = defaultdict(set)
    for topic, nodes in topic_learned.items():
        for node in nodes:
            learned_titles_by_topic[topic].add(node.concept)

    # Add recommended concepts (deduplicated against learned)
    topic_recommended: dict[str, list[ConceptNode]] = defaultdict(list)
    seen_recommendations: dict[str, set[str]] = defaultdict(set)

    for entry in sorted(graph_entries, key=lambda e: e.created_at):
        topic = entry.topic
        learned_set = learned_titles_by_topic.get(topic, set())
        for rec in (entry.recommended_concepts or []):
            title = rec.get("title", "")
            if title and title not in learned_set and title not in seen_recommendations[topic]:
                seen_recommendations[topic].add(title)
                topic_recommended[topic].append(ConceptNode(
                    concept=title,
                    status="recommended",
                    reason=rec.get("reason"),
                    prerequisite_concepts=entry.learned_concepts or [],
                ))

    # Merge into final response
    all_topics = set(topic_learned.keys()) | set(topic_recommended.keys())
    topics = []
    for topic in sorted(all_topics):
        nodes = topic_learned.get(topic, []) + topic_recommended.get(topic, [])
        topics.append(KnowledgeMapTopic(topic=topic, nodes=nodes))

    return KnowledgeMapResponse(topics=topics)


@router.post("/quiz/generate", response_model=GenerateQuizResponse)
async def generate_quiz(
    data: GenerateQuizRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await learning_service.generate_quiz_for_module(data.module_id, db)


@router.post("/quiz/submit", response_model=SubmitQuizResponse)
async def submit_quiz(
    data: SubmitQuizRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await quiz_service.score_quiz(data.quiz_id, data.answers, db, data.local_date)
    return SubmitQuizResponse(**result)


@router.post("/remediate", response_model=RemediateResponse)
async def remediate(
    data: RemediateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not data.failed_concepts:
        raise HTTPException(status_code=400, detail="No failed concepts provided")
    return await learning_service.remediate(data.module_id, data.quiz_id, data.failed_concepts, db)
