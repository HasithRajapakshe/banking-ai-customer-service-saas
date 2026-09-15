from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ToolExecutionContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    customer_id: UUID

    user_id: UUID | None = None
    conversation_id: UUID | None = None

    correlation_id: str
    channel: str | None = None