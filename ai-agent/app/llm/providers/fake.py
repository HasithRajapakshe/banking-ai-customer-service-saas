"""Scripted provider for tests and CI: no network, no API key.

Responses are chosen by a responder function, or from a mapping of user
message -> response. Scripts can return an LLMResponse or raise (to simulate
outages), which lets tests exercise every fallback path.
"""

from collections.abc import Callable
from typing import Any

from app.llm.base import ChatMessage, LLMError, LLMResponse, ToolSpec

Responder = Callable[[list[ChatMessage], list[ToolSpec] | None], LLMResponse]


class FakeProvider:
    name = "fake"

    def __init__(
        self,
        responder: Responder | None = None,
        *,
        script: dict[str, Any] | None = None,
        default: LLMResponse | None = None,
    ):
        self._responder = responder
        self._script = script or {}
        self._default = default or LLMResponse()
        self.calls: list[tuple[list[ChatMessage], list[ToolSpec] | None]] = []

    async def achat(self, messages: list[ChatMessage], tools: list[ToolSpec] | None = None) -> LLMResponse:
        self.calls.append((messages, tools))
        if self._responder is not None:
            return self._responder(messages, tools)

        user_text = next((m.content for m in reversed(messages) if m.role == "user"), "")
        scripted = self._script.get(user_text, self._default)
        if isinstance(scripted, Exception):
            raise scripted
        if isinstance(scripted, LLMResponse):
            return scripted
        raise LLMError(f"Unsupported fake script entry: {scripted!r}")
