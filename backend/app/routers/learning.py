from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.learning import ConceptGraph, Module, Passage, TopicEdge, TopicNode
from app.models.user import User
from app.schemas.learning import (
    ConceptNode,
    GenerateQuizRequest,
    GenerateQuizResponse,
    KnowledgeDomain,
    KnowledgeGraphResponse,
    KnowledgeMapResponse,
    KnowledgeMapTopic,
    RemediateRequest,
    RemediateResponse,
    StartModuleRequest,
    StartModuleResponse,
    SubmitQuizRequest,
    SubmitQuizResponse,
    TopicEdgeResponse,
    TopicNodeResponse,
)
from app.services import learning_service, quiz_service, recommendation_service

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


@router.post("/recommendations/backfill")
async def backfill_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await recommendation_service.backfill_for_user(current_user.id, db)
    return {"backfilled": count}


@router.get("/knowledge-map", response_model=KnowledgeGraphResponse)
async def get_knowledge_map(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Fetch all topic_nodes for this user
    nodes_result = await db.execute(
        select(TopicNode).where(TopicNode.user_id == current_user.id)
    )
    nodes = nodes_result.scalars().all()

    # Fetch all topic_edges for this user
    edges_result = await db.execute(
        select(TopicEdge).where(TopicEdge.user_id == current_user.id)
    )
    edges = edges_result.scalars().all()

    # Group nodes by domain
    domain_map: dict[str, list[TopicNodeResponse]] = defaultdict(list)
    for node in nodes:
        domain_key = node.domain or "General"
        hints = node.concept_hints if isinstance(node.concept_hints, list) else None
        domain_map[domain_key].append(TopicNodeResponse(
            id=str(node.id),
            canonical_name=node.canonical_name,
            display_name=node.display_name,
            domain=node.domain,
            status=node.status,
            source_module_id=str(node.source_module_id) if node.source_module_id else None,
            concept_hints=hints,
            reason=node.reason,
        ))

    domains = [
        KnowledgeDomain(name=name, nodes=domain_nodes)
        for name, domain_nodes in sorted(domain_map.items())
    ]

    edge_responses = [
        TopicEdgeResponse(
            source_id=str(e.source_node_id),
            target_id=str(e.target_node_id),
            relationship_type=e.relationship_type,
        )
        for e in edges
    ]

    return KnowledgeGraphResponse(domains=domains, edges=edge_responses)


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
