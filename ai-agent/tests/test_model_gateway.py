import asyncio
import logging
from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from app.llm.base import ChatMessage, LLMError, LLMResponse, LLMUnavailable, ToolCall, ToolSpec
from app.llm.gateway import ModelGateway, build_model_gateway
from app.llm.providers.fake import FakeProvider

USER = [ChatMessage(role="user", content="hi")]


def settings(**overrides):
    base = dict(
        model_provider="deterministic", model_name="m", ollama_base_url="http://localhost:11434", ollama_num_ctx=8192,
        google_api_key=None, openai_api_key=None, anthropic_api_key=None,
        llm_timeout_seconds=5.0, llm_max_retries=1, llm_temperature=0.0,
    )
    return SimpleNamespace(**{**base, **overrides})


class Flaky:
    """Fails `failures` times, then answers."""

    name = "flaky"

    def __init__(self, failures: int, error: Exception | None = None, delay: float = 0.0):
        self.failures, self.error, self.delay, self.calls = failures, error, delay, 0

    async def achat(self, messages, tools=None):
        self.calls += 1
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.calls <= self.failures:
            raise self.error or LLMError("boom")
        return LLMResponse(content="ok")


@pytest.mark.asyncio
async def test_retries_then_succeeds(caplog):
    provider = Flaky(failures=1)
    gateway = ModelGateway(provider, max_retries=1, backoff_seconds=0)

    with caplog.at_level(logging.WARNING, logger="ai_agent.llm"):
        response = await gateway.chat(USER)

    assert response.content == "ok"
    assert provider.calls == 2
    assert "attempt 1/2" in caplog.text  # the failure was logged, not swallowed


@pytest.mark.asyncio
async def test_gives_up_with_llm_unavailable():
    gateway = ModelGateway(Flaky(failures=5), max_retries=2, backoff_seconds=0)
    with pytest.raises(LLMUnavailable):
        await gateway.chat(USER)


@pytest.mark.asyncio
async def test_timeout_counts_as_failure():
    provider = Flaky(failures=0, delay=1.0)
    gateway = ModelGateway(provider, timeout_seconds=0.05, max_retries=0)
    with pytest.raises(LLMUnavailable, match="timed out"):
        await gateway.chat(USER)


@pytest.mark.asyncio
async def test_tools_are_passed_to_provider():
    tool = ToolSpec(name="card.list", description="List cards", parameters={"type": "object", "properties": {}})
    fake = FakeProvider(default=LLMResponse(tool_calls=(ToolCall(name="card.list"),)))
    response = await ModelGateway(fake).chat(USER, [tool])

    assert response.tool_calls[0].name == "card.list"
    assert fake.calls[0][1] == [tool]


class Answer(BaseModel):
    answer: str
    cited: list[str]


@pytest.mark.asyncio
async def test_structured_output_is_parsed_and_validated():
    fake = FakeProvider(default=LLMResponse(content='Sure: {"answer": "Block it", "cited": ["Card policy"]}'))
    result = await ModelGateway(fake).structured(USER, Answer)
    assert result == Answer(answer="Block it", cited=["Card policy"])


@pytest.mark.asyncio
@pytest.mark.parametrize("content", ["no json here", '{"answer": 3}'])
async def test_invalid_structured_output_raises(content):
    fake = FakeProvider(default=LLMResponse(content=content))
    with pytest.raises(LLMUnavailable):
        await ModelGateway(fake, max_retries=0).structured(USER, Answer)


def test_deterministic_means_no_gateway():
    assert build_model_gateway(settings(model_provider="deterministic")) is None


def test_fake_provider_needs_no_key_or_network():
    gateway = build_model_gateway(settings(model_provider="fake"))
    assert gateway is not None
    assert gateway.provider_name == "fake"


@pytest.mark.parametrize("provider", ["gemini", "openai", "anthropic"])
def test_missing_api_key_disables_provider_and_logs(provider, caplog):
    with caplog.at_level(logging.ERROR, logger="ai_agent.llm"):
        assert build_model_gateway(settings(model_provider=provider)) is None
    assert "could not be initialised" in caplog.text


def test_unknown_provider_is_disabled(caplog):
    with caplog.at_level(logging.ERROR, logger="ai_agent.llm"):
        assert build_model_gateway(settings(model_provider="skynet")) is None


def test_ollama_provider_builds_without_network():
    gateway = build_model_gateway(settings(model_provider="ollama", model_name="qwen2.5:7b"))
    assert gateway is not None
    assert gateway.provider_name == "ollama"
