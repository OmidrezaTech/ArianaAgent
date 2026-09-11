from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database.session import get_db
from src.infrastructure.database.models import User
from src.application.brain_service import BrainService
from src.domain.schemas.brain_schemas import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentResponse,
    DecisionCreate,
    DecisionResponse,
    MemoryCreate,
    MemoryResponse,
)
from src.api.dependencies import get_current_user

router = APIRouter(prefix="/brain", tags=["Company Brain & Memory"])


@router.post("/documents", response_model=KnowledgeDocumentResponse, status_code=status.HTTP_201_CREATED)
async def add_knowledge_document(
    data: KnowledgeDocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = BrainService(db)
    return await service.add_document(data, user_id=current_user.id)


@router.get("/search")
async def search_brain(
    query: str = Query(..., min_length=2),
    project_id: Optional[str] = None,
    top_k: int = 5,
    db: AsyncSession = Depends(get_db),
):
    service = BrainService(db)
    return await service.search(query=query, project_id=project_id, top_k=top_k)


@router.post("/decisions", response_model=DecisionResponse, status_code=status.HTTP_201_CREATED)
async def record_decision(
    data: DecisionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = BrainService(db)
    data.decided_by_user = current_user.id
    return await service.record_decision(data)


@router.get("/memories", response_model=List[MemoryResponse])
async def list_memories(
    project_id: str,
    agent_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    service = BrainService(db)
    return await service.list_memories(project_id=project_id, agent_id=agent_id)
