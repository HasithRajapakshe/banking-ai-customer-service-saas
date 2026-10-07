from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    message: str
    tenant_id: str
    customer_id: str
    user_id: str | None
    conversation_id: str
    channel: str
    confirmed: bool
    correlation_id: str
    tool_name_override: str | None
    tool_arguments_override: dict[str, Any]

    security_allowed: bool
    intent: str
    route: str
    tool_name: str | None
    tool_arguments: dict[str, Any]
    clarification: str | None
    tool_calls: int
    tool_result: dict[str, Any] | None

    status: str
    response_message: str
    requires_confirmation: bool
