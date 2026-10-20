import pytest

from app.llm.base import LLMError, LLMResponse
from app.llm.gateway import ModelGateway
from app.llm.providers.fake import FakeProvider
from app.services.rag_answer import NO_INFORMATION, answer_question

DOCS = [
    {"title": "Lost or Stolen Card Procedure", "content": "Report a lost card immediately; the bank may block it."},
    {"title": "KYC Requirements", "content": "Customers may need a national identity document."},
]


class RealishProvider(FakeProvider):
    """A non-fake provider name, so answer_question uses the model."""

    name = "ollama"


def gateway(response=None, error=None) -> ModelGateway:
    script = {"what if I lose my card?": error} if error else {}
    return ModelGateway(RealishProvider(default=response, script=script), max_retries=0, backoff_seconds=0)


@pytest.mark.asyncio
async def test_no_chunks_means_no_information():
    assert await answer_question("anything", [], gateway(LLMResponse(content="made up"))) == (NO_INFORMATION, [])


@pytest.mark.asyncio
@pytest.mark.parametrize("gw", [None, ModelGateway(FakeProvider())])
async def test_no_model_or_fake_provider_keeps_deterministic_answer(gw):
    answer, cited = await answer_question("lost card?", DOCS, gw)
    assert answer.startswith("Based on our policy 'Lost or Stolen Card Procedure'")
    assert cited == ["Lost or Stolen Card Procedure"]


@pytest.mark.asyncio
async def test_model_answer_with_citation_is_used():
    reply = "Report it immediately so the bank can block it [Lost or Stolen Card Procedure]."
    answer, cited = await answer_question("what if I lose my card?", DOCS, gateway(LLMResponse(content=reply)))
    assert answer == reply
    assert cited == ["Lost or Stolen Card Procedure"]


@pytest.mark.asyncio
async def test_uncited_model_answer_is_replaced():
    answer, _ = await answer_question("what if I lose my card?", DOCS, gateway(LLMResponse(content="Just call us.")))
    assert answer.startswith("Based on our policy")


@pytest.mark.asyncio
async def test_model_saying_it_does_not_know_is_respected():
    answer, cited = await answer_question(
        "what if I lose my card?", DOCS, gateway(LLMResponse(content="I don't have that information."))
    )
    assert (answer, cited) == (NO_INFORMATION, [])


@pytest.mark.asyncio
async def test_model_failure_falls_back_to_deterministic():
    answer, _ = await answer_question("what if I lose my card?", DOCS, gateway(error=LLMError("down")))
    assert answer.startswith("Based on our policy")
