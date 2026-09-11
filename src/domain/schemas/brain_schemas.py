from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict
from src.infrastructure.database.models import DocumentType, MemoryType


class KnowledgeDocumentCreate(BaseModel):
    project_id: Optional[str] = None
    title: str
    document_type: DocumentType
    content: str
    source: Optional[str] = None


class KnowledgeDocumentResponse(BaseModel):
    id: str
    project_id: Optional[str] = None
    title: str
    document_type: DocumentType
    content: str
    source: Optional[str] = None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeSearchResult(BaseModel):
    document_id: str
    chunk_index: int
    content: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DecisionCreate(BaseModel):
    project_id: str
    request_id: Optional[str] = None
    title: str
    decision: str
    reason: Optional[str] = None
    decided_by_type: str = "HUMAN"  # HUMAN or AI
    decided_by_user: Optional[str] = None
    agent_run_id: Optional[str] = None


class DecisionResponse(BaseModel):
    id: str
    project_id: str
    request_id: Optional[str] = None
    title: str
    decision: str
    reason: Optional[str] = None
    decided_by_type: str
    decided_by_user: Optional[str] = None
    agent_run_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemoryCreate(BaseModel):
    project_id: str
    agent_id: str
    memory_type: MemoryType
    content: str
    importance: int = Field(default=5, ge=1, le=10)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemoryResponse(BaseModel):
    id: str
    project_id: str
    agent_id: str
    memory_type: MemoryType
    content: str
    importance: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

