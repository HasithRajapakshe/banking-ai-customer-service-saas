import hashlib
import logging
import math
import re

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from app.core.config import settings
from app.models import EMBEDDING_DIMENSIONS

logger = logging.getLogger("rag.embeddings")

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset(
    "a an and are as at be by can do does for from has have how i if in is it its me my "
    "of on or our the this to was what when where which who why will with you your".split()
)
_PLACEHOLDER_KEY_MARKERS = ("your", "change", "placeholder", "xxx", "replace")


class MockEmbeddings(Embeddings):
    """Deterministic, offline embeddings via feature hashing.

    Each non-stopword token is hashed to one of `dimensions` slots with a +/-1
    sign, and the vector is L2-normalised. The same text always yields the
    same vector, and cosine similarity reflects shared vocabulary, so search
    ranking is meaningful without an external provider.
    """

    def __init__(self, dimensions: int = EMBEDDING_DIMENSIONS):
        self.dimensions = dimensions

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in _TOKEN_RE.findall(text.lower()):
            if token in _STOPWORDS:
                continue
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(v * v for v in vector))
        if norm == 0.0:
            # No usable tokens: return a fixed unit vector (a zero vector has
            # no defined cosine distance).
            vector[0] = 1.0
            return vector
        return [v / norm for v in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


def _is_usable_api_key(key: str | None) -> bool:
    if not key or not key.strip():
        return False
    lowered = key.strip().lower()
    if lowered in ("sk-", "sk-...") or any(marker in lowered for marker in _PLACEHOLDER_KEY_MARKERS):
        return False
    return True


def get_embeddings() -> Embeddings:
    provider = settings.embedding_provider.lower()
    if provider == "openai":
        if _is_usable_api_key(settings.openai_api_key):
            return OpenAIEmbeddings(
                model=settings.embedding_model,
                openai_api_key=settings.openai_api_key,
            )
        logger.warning(
            "EMBEDDING_PROVIDER=openai but OPENAI_API_KEY is missing or a placeholder; "
            "falling back to deterministic mock embeddings."
        )
    elif provider != "mock":
        logger.warning("Unknown EMBEDDING_PROVIDER=%r; using mock embeddings.", settings.embedding_provider)
    return MockEmbeddings()


class RAGService:
    def __init__(self):
        self.embeddings = get_embeddings()

    async def get_embedding(self, text: str) -> list[float]:
        """Get the embedding vector for a single query."""
        return await self.embeddings.aembed_query(text)

    async def get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        return await self.embeddings.aembed_documents(texts)


rag_service = RAGService()
