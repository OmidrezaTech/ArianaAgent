from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database.models import DocumentType, MemoryType, Decision, Memory, KnowledgeDocument
from src.infrastructure.brain.knowledge_service import KnowledgeService
from src.domain.schemas.brain_schemas import KnowledgeDocumentCreate, DecisionCreate, MemoryCreate


class BrainService:
    """Application facade for Company Brain operations"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.knowledge_svc = KnowledgeService(session)

    async def add_document(self, data: KnowledgeDocumentCreate, user_id: Optional[str] = None) -> KnowledgeDocument:
        return await self.knowledge_svc.ingest_document(
            title=data.title,
            document_type=data.document_type,
            content=data.content,
            project_id=data.project_id,
            source=data.source,
            created_by=user_id,
        )

    async def search(self, query: str, project_id: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        return await self.knowledge_svc.search_context(query=query, project_id=project_id, top_k=top_k)

    async def record_decision(self, data: DecisionCreate) -> Decision:
        return await self.knowledge_svc.log_decision(
            project_id=data.project_id,
            title=data.title,
            decision=data.decision,
            reason=data.reason,
            decided_by_type=data.decided_by_type,
            decided_by_user=data.decided_by_user,
            agent_run_id=data.agent_run_id,
            request_id=data.request_id,
        )

    async def record_memory(self, data: MemoryCreate) -> Memory:
        return await self.knowledge_svc.save_memory(
            project_id=data.project_id,
            agent_id=data.agent_id,
            memory_type=data.memory_type,
            content=data.content,
            importance=data.importance,
            metadata=data.metadata,
        )

    async def list_memories(self, project_id: str, agent_id: Optional[str] = None) -> List[Memory]:
        return await self.knowledge_svc.get_memories(project_id=project_id, agent_id=agent_id)
