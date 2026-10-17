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
    # Code issued by the Tool Gateway for a pending HIGH/CRITICAL action.
    challenge_code: str | None = Field(default=None, max_length=64)

    # Internal API only: the API Gateway replays a server-stored pending
    # action here when the user confirms. Browsers cannot set these (the
    # public API Gateway request has no such fields), and they never bypass
    # Tool Gateway authorization or confirmation controls.
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
    # Set when requires_confirmation is true.
    confirmation_challenge: str | None = None
    action_summary: str | None = None
    tool_arguments: dict[str, Any] | None = None
    data: Any | None = None
