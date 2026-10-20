"""Model gateway: one async entry point for every provider.

Adds a per-call timeout and retries with backoff, logs every failure, and
raises LLMUnavailable when it gives up so callers can fall back to
deterministic behaviour. It never swallows an error silently.
"""

import asyncio
import json
import logging
import re
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from app.llm.base import ChatMessage, ChatProvider, LLMError, LLMResponse, LLMUnavailable, ToolSpec

logger = logging.getLogger("ai_agent.llm")

T = TypeVar("T", bound=BaseModel)

NO_LLM_PROVIDERS = frozenset({"deterministic", "none", ""})
_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


class ModelGateway:
    def __init__(
        self,
        provider: ChatProvider,
        *,
        timeout_seconds: float = 60.0,
        max_retries: int = 1,
        backoff_seconds: float = 0.5,
    ):
        self.provider = provider
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds

    @property
    def provider_name(self) -> str:
        return self.provider.name

    async def chat(self, messages: list[ChatMessage], tools: list[ToolSpec] | None = None) -> LLMResponse:
        attempts = self.max_retries + 1
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                return await asyncio.wait_for(self.provider.achat(messages, tools), self.timeout_seconds)
            except asyncio.TimeoutError:
                last_error = LLMError(f"timed out after {self.timeout_seconds}s")
            except LLMError as exc:
                last_error = exc
            logger.warning(
                "LLM call failed (provider=%s, attempt %d/%d): %s",
                self.provider.name, attempt, attempts, last_error,
            )
            if attempt < attempts:
                await asyncio.sleep(self.backoff_seconds * attempt)
        raise LLMUnavailable(f"{self.provider.name} unavailable: {last_error}") from last_error

    async def structured(self, messages: list[ChatMessage], schema: type[T]) -> T:
        """Ask for JSON matching `schema`; validate it. Raises LLMUnavailable on failure."""
        instruction = ChatMessage(
            role="system",
            content=(
                "Respond with a single JSON object only, no prose, matching this JSON Schema:\n"
                + json.dumps(schema.model_json_schema())
            ),
        )
        response = await self.chat([*messages, instruction])
        match = _JSON_BLOCK.search(response.content or "")
        try:
            if match is None:
                raise ValueError("no JSON object in response")
            return schema.model_validate_json(match.group(0))
        except (ValueError, ValidationError) as exc:
            logger.warning("LLM structured output invalid (provider=%s): %s", self.provider.name, exc)
            raise LLMUnavailable(f"invalid structured output: {exc}") from exc


def build_model_gateway(settings: Any) -> ModelGateway | None:
    """Gateway for the configured provider, or None for the keyword-only mode.

    A misconfigured provider (missing package or key) is logged and disabled
    rather than crashing the service: the agent then runs deterministically.
    """
    provider_name = (settings.model_provider or "").lower()
    if provider_name in NO_LLM_PROVIDERS:
        return None
    try:
        if provider_name == "fake":
            from app.llm.providers.fake import FakeProvider

            provider: ChatProvider = FakeProvider()
        else:
            from app.llm.providers.langchain_provider import LangChainProvider

            provider = LangChainProvider(provider_name, settings.model_name, settings)
    except Exception as exc:
        logger.error(
            "Model provider %r could not be initialised; using the keyword router only: %s",
            provider_name, exc,
        )
        return None

    logger.info("Model gateway: provider=%s model=%s", provider_name, settings.model_name)
    return ModelGateway(
        provider,
        timeout_seconds=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
    )
