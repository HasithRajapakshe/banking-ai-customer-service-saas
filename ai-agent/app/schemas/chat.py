from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


AgentStatus = Literal[
    "completed",
    "needs_clarification",
    "confirmation_required",
    "blocked",
    "failed",
]


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=8000)
    tenant_id: UUID
    customer_id: UUID
    user_id: UUID | None = None
    conversation_id: UUID = Field(default_factory=uuid4)
    channel: str = Field(default="web", max_length=50)
    confirmed: bool = False

    # Optional deterministic override for integration tests / trusted clients.
    # It never bypasses Tool Gateway authorization or confirmation controls.
    tool_name: str | None = None
    tool_arguments: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conversation_id: UUID
    correlation_id: str
    status: AgentStatus
    message: str
    intent: str
    tool_name: str | None = None
    tool_executed: bool = False
    requires_confirmation: bool = False
    data: Any | None = None
