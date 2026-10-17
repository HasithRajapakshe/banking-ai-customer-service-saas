"""Provider-agnostic types for the model gateway."""

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

Role = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class ChatMessage:
    role: Role
    content: str


@dataclass(frozen=True)
class ToolSpec:
    """A tool the model may call; `parameters` is a JSON Schema object."""

    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LLMResponse:
    content: str = ""
    tool_calls: tuple[ToolCall, ...] = ()


class LLMError(Exception):
    """A provider call failed (network, auth, malformed output, ...)."""


class LLMUnavailable(LLMError):
    """The gateway gave up after timeouts/retries; callers must fall back."""


class ChatProvider(Protocol):
    name: str

    async def achat(
        self,
        messages: list[ChatMessage],
        tools: list[ToolSpec] | None = None,
    ) -> LLMResponse:
        """One model call. Raises LLMError on failure."""
        ...
