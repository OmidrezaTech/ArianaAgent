from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database.models import (
    KnowledgeDocument,
    KnowledgeChunk,
    DocumentType,
    Memory,
    MemoryType,
    Decision,
)
from src.infrastructure.database.repositories.brain_repo import (
    KnowledgeDocumentRepository,
    KnowledgeChunkRepository,
    DecisionRepository,
    MemoryRepository,
)
from src.infrastructure.brain.embedding_service import EmbeddingService
from src.core.config import settings
from src.core.logging import logger


class KnowledgeService:
    """Company Brain & Memory Subsystem (RAG, Vector Search, Decisions, Memories)"""

    def __init__(self, session: AsyncSession, embedding_service: Optional[EmbeddingService] = None):
        self.session = session
        self.embeddings = embedding_service or EmbeddingService()
        self.doc_repo = KnowledgeDocumentRepository(session)
        self.chunk_repo = KnowledgeChunkRepository(session)
        self.decision_repo = DecisionRepository(session)
        self.memory_repo = MemoryRepository(session)

    async def ingest_document(
        self,
        title: str,
        document_type: DocumentType,
        content: str,
        project_id: Optional[str] = None,
        source: Optional[str] = None,
        created_by: Optional[str] = None,
        chunk_size: int = 500,
    ) -> KnowledgeDocument:
        doc = KnowledgeDocument(
            project_id=project_id,
            title=title,
            document_type=document_type,
            content=content,
            source=source,
            created_by=created_by,
        )
        saved_doc = await self.doc_repo.create(doc)

        # Split into chunks and embed
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [content]

        for idx, chunk_text in enumerate(paragraphs):
            emb = await self.embeddings.embed_text(chunk_text)
            chunk = KnowledgeChunk(
                document_id=saved_doc.id,
                content=chunk_text,
                chunk_index=idx,
                embedding=emb,
                metadata_={"title": title, "doc_type": document_type.value, "chunk_index": idx},
            )
            await self.chunk_repo.create(chunk)

        logger.info("document_ingested", title=title, chunks=len(paragraphs), doc_id=saved_doc.id)
        return saved_doc

    async def search_context(
        self,
        query: str,
        project_id: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        query_emb = await self.embeddings.embed_text(query)
        results = await self.chunk_repo.search_vector(
            query_embedding=query_emb,
            project_id=project_id,
            top_k=top_k,
            is_postgres=settings.is_postgres,
        )
        return [
            {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "content": chunk.content,
                "score": round(score, 4),
                "metadata": chunk.metadata_,
            }
            for chunk, score in results
        ]

    async def save_memory(
        self,
        project_id: str,
        agent_id: str,
        memory_type: MemoryType,
        content: str,
        importance: int = 5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Memory:
        mem = Memory(
            project_id=project_id,
            agent_id=agent_id,
            memory_type=memory_type,
            content=content,
            importance=importance,
            metadata_=metadata or {},
        )
        return await self.memory_repo.create(mem)

    async def get_memories(
        self, project_id: str, agent_id: Optional[str] = None, limit: int = 10
    ) -> List[Memory]:
        return await self.memory_repo.list_by_project_and_agent(project_id, agent_id, limit=limit)

    async def log_decision(
        self,
        project_id: str,
        title: str,
        decision: str,
        reason: Optional[str] = None,
        decided_by_type: str = "AI",
        decided_by_user: Optional[str] = None,
        agent_run_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Decision:
        dec = Decision(
            project_id=project_id,
            request_id=request_id,
            title=title,
            decision=decision,
            reason=reason,
            decided_by_type=decided_by_type,
            decided_by_user=decided_by_user,
            agent_run_id=agent_run_id,
        )
        return await self.decision_repo.create(dec)
