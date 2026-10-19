"""The API Gateway's internal identity token for the current request.

The agent does not mint or interpret it: it forwards it unchanged to the Tool
Gateway and RAG, which verify it and take identity only from it. A context
variable carries it to the HTTP clients without threading it through the
LangGraph state (where it would be checkpointed).
"""

from contextvars import ContextVar

INTERNAL_TOKEN_HEADER = "X-Internal-Token"

current_internal_token: ContextVar[str | None] = ContextVar("current_internal_token", default=None)


def internal_token_headers() -> dict[str, str]:
    token = current_internal_token.get()
    return {INTERNAL_TOKEN_HEADER: token} if token else {}
