import logging
import math

import pytest
from langchain_openai import OpenAIEmbeddings

from app.core.config import settings
from app.models import EMBEDDING_DIMENSIONS
from app.services import rag_service as rag_service_module
from app.services.rag_service import MockEmbeddings, get_embeddings


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))  # vectors are unit length


def test_mock_embeddings_are_deterministic_and_sized():
    emb = MockEmbeddings()
    first = emb.embed_query("How do I block a lost card?")
    second = MockEmbeddings().embed_query("How do I block a lost card?")

    assert first == second
    assert len(first) == EMBEDDING_DIMENSIONS == 1536
    assert math.isclose(math.sqrt(sum(v * v for v in first)), 1.0, rel_tol=1e-9)


def test_different_texts_get_different_vectors():
    emb = MockEmbeddings()
    assert emb.embed_query("card fees") != emb.embed_query("loan interest rates")


def test_similarity_ranks_related_text_higher():
    emb = MockEmbeddings()
    query = emb.embed_query("What should I do if my card is lost or stolen?")
    card_doc = emb.embed_documents(
        ["Lost or stolen card procedure: block the card immediately and request a replacement card."]
    )[0]
    loan_doc = emb.embed_documents(
        ["Home loan eligibility depends on income, employment history and the property valuation."]
    )[0]

    assert cosine(query, card_doc) > cosine(query, loan_doc)
    assert cosine(query, card_doc) >= settings.search_similarity_threshold


def test_text_without_tokens_is_still_a_unit_vector():
    vector = MockEmbeddings().embed_query("?!")
    assert math.isclose(sum(v * v for v in vector), 1.0)


@pytest.mark.parametrize("key", [None, "", "  ", "sk-...", "your-openai-api-key", "changeme"])
def test_openai_without_usable_key_falls_back_to_mock(monkeypatch, caplog, key):
    monkeypatch.setattr(rag_service_module.settings, "embedding_provider", "openai")
    monkeypatch.setattr(rag_service_module.settings, "openai_api_key", key)

    with caplog.at_level(logging.WARNING, logger="rag.embeddings"):
        embeddings = get_embeddings()

    assert isinstance(embeddings, MockEmbeddings)
    assert "falling back" in caplog.text


def test_openai_with_key_uses_openai(monkeypatch):
    monkeypatch.setattr(rag_service_module.settings, "embedding_provider", "openai")
    monkeypatch.setattr(rag_service_module.settings, "openai_api_key", "sk-test-0123456789abcdef")

    assert isinstance(get_embeddings(), OpenAIEmbeddings)
