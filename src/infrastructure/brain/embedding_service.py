import hashlib
import math
from typing import List
import httpx
from src.core.config import settings
from src.core.logging import logger


class EmbeddingService:
    """Provides vector embeddings for semantic search in pgvector / memory search"""

    def __init__(self, dimension: int = 1536):
        self.dimension = dimension

    async def embed_text(self, text: str) -> List[float]:
        # Try OpenAI Embeddings if key configured
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "mock-key":
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    res = await client.post(
                        "https://api.openai.com/v1/embeddings",
                        headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                        json={"input": text, "model": "text-embedding-3-small"},
                    )
                    if res.status_code == 200:
                        data = res.json()
                        return data["data"][0]["embedding"]
            except Exception as e:
                logger.warning("openai_embedding_fallback", error=str(e))

        # Deterministic synthetic embedding vector (1536-dimensional unit vector)
        return self._generate_synthetic_embedding(text)

    def _generate_synthetic_embedding(self, text: str) -> List[float]:
        words = text.lower().split()
        vector = [0.0] * self.dimension
        for word in words:
            # Hash each token to multiple feature buckets
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            for i in range(4):
                idx = (h + (i * 383)) % self.dimension
                val = 1.0 if ((h >> i) & 1) else -1.0
                vector[idx] += val

        # Normalize to unit length
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        else:
            vector[0] = 1.0
        return vector
