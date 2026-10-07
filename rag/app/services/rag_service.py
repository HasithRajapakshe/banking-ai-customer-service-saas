import uuid
from typing import Any

from langchain_core.documents import Document as LangchainDocument
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from app.core.config import settings
from app.models import Document, DocumentChunk


class MockEmbeddings(Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        # Mock embedding of size 1536
        return [[0.1] * 1536 for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return [0.1] * 1536


def get_embeddings() -> Embeddings:
    if settings.embedding_provider == "openai" and settings.openai_api_key:
        return OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key,
        )
    return MockEmbeddings()


class RAGService:
    def __init__(self):
        self.embeddings = get_embeddings()
    
    async def get_embedding(self, text: str) -> list[float]:
        """Get the embedding vector for a single query."""
        # This is a synchronous call to the embeddings provider in langchain,
        # but in a production async app we'd use aget_embedding if available.
        # Langchain provides async methods as well.
        if hasattr(self.embeddings, "aembed_query"):
            return await self.embeddings.aembed_query(text)
        return self.embeddings.embed_query(text)

    async def get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        if hasattr(self.embeddings, "aembed_documents"):
            return await self.embeddings.aembed_documents(texts)
        return self.embeddings.embed_documents(texts)


rag_service = RAGService()
