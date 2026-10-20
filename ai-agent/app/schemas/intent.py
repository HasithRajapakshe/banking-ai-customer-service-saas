from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


IntentRoute = Literal["tool", "general", "blocked", "clarify"]


class IntentDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: str
    route: IntentRoute
    tool_name: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)
    clarification: str | None = None
