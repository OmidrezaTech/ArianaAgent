import math
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload
from src.infrastructure.database.models import (
    KnowledgeDocument,
    KnowledgeChunk,
    Decision,
    Memory,
)
from src.infrastructure.database.repositories.base_repo import BaseRepository


class KnowledgeDocumentRepository(BaseRepository[KnowledgeDocument]):
    def __init__(self, session: AsyncSession):
        super().__init__(KnowledgeDocument, session)

    async def get_with_chunks(self, document_id: str) -> Optional[KnowledgeDocument]:
        result = await self.session.execute(
            select(KnowledgeDocument)
            .options(selectinload(KnowledgeDocument.chunks))
            .where(KnowledgeDocument.id == document_id)
        )
        return result.scalars().first()

    async def list_by_project(self, project_id: Optional[str]) -> List[KnowledgeDocument]:
        query = select(KnowledgeDocument)
        if project_id:
            query = query.where((KnowledgeDocument.project_id == project_id) | (KnowledgeDocument.project_id == None))
        result = await self.session.execute(query)
        return list(result.scalars().all())


class KnowledgeChunkRepository(BaseRepository[KnowledgeChunk]):
    def __init__(self, session: AsyncSession):
        super().__init__(KnowledgeChunk, session)

    async def search_vector(
        self,
        query_embedding: List[float],
        project_id: Optional[str] = None,
        top_k: int = 5,
        is_postgres: bool = False,
    ) -> List[Tuple[KnowledgeChunk, float]]:
        """Semantic search with cosine similarity"""
        if is_postgres:
            # Native PostgreSQL pgvector cosine distance: embedding <=> query_embedding
            str_emb = "[" + ",".join(map(str, query_embedding)) + "]"
            sql = f"""
                SELECT c.id, c.document_id, c.content, c.chunk_index, c.metadata,
                       1 - (c.embedding <=> '{str_emb}'::vector) AS similarity
                FROM knowledge_chunks c
                JOIN knowledge_documents d ON c.document_id = d.id
                WHERE (d.project_id = :project_id OR d.project_id IS NULL)
                ORDER BY c.embedding <=> '{str_emb}'::vector ASC
                LIMIT :limit
            """
            result = await self.session.execute(text(sql), {"project_id": project_id, "limit": top_k})
            rows = result.fetchall()
            output = []
            for row in rows:
                chunk = KnowledgeChunk(
                    id=row[0],
                    document_id=row[1],
                    content=row[2],
                    chunk_index=row[3],
                    metadata_=row[4],
                )
                output.append((chunk, float(row[5])))
            return output
        else:
            # In-memory cosine similarity fallback for SQLite / testing
            query = select(KnowledgeChunk).join(KnowledgeDocument)
            if project_id:
                query = query.where((KnowledgeDocument.project_id == project_id) | (KnowledgeDocument.project_id == None))
            result = await self.session.execute(query)
            chunks = result.scalars().all()

            def cosine_similarity(v1: List[float], v2: List[float]) -> float:
                if not v1 or not v2 or len(v1) != len(v2):
                    return 0.0
                dot = sum(a * b for a, b in zip(v1, v2))
                norm1 = math.sqrt(sum(a * a for a in v1))
                norm2 = math.sqrt(sum(b * b for b in v2))
                if norm1 == 0 or norm2 == 0:
                    return 0.0
                return dot / (norm1 * norm2)

            scored = []
            for chunk in chunks:
                if chunk.embedding:
                    sim = cosine_similarity(query_embedding, chunk.embedding)
                    scored.append((chunk, sim))
                else:
                    scored.append((chunk, 0.5))

            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:top_k]


class DecisionRepository(BaseRepository[Decision]):
    def __init__(self, session: AsyncSession):
        super().__init__(Decision, session)

    async def list_by_project(self, project_id: str) -> List[Decision]:
        result = await self.session.execute(
            select(Decision)
            .where(Decision.project_id == project_id)
            .order_by(Decision.created_at.desc())
        )
        return list(result.scalars().all())


class MemoryRepository(BaseRepository[Memory]):
    def __init__(self, session: AsyncSession):
        super().__init__(Memory, session)

    async def list_by_project_and_agent(
        self, project_id: str, agent_id: Optional[str] = None, limit: int = 20
    ) -> List[Memory]:
        query = select(Memory).where(Memory.project_id == project_id)
        if agent_id:
            query = query.where(Memory.agent_id == agent_id)
        query = query.order_by(Memory.importance.desc(), Memory.created_at.desc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
