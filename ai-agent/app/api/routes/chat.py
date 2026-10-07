from fastapi import APIRouter, Request

from app.graph.workflow import agent_graph
from app.schemas.chat import ChatRequest, ChatResponse


router = APIRouter(prefix="/api/v1/agent", tags=["AI Agent"])


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request):
    state = await agent_graph.ainvoke(
        {
            "message": payload.message,
            "tenant_id": str(payload.tenant_id),
            "customer_id": str(payload.customer_id),
            "user_id": str(payload.user_id) if payload.user_id else None,
            "conversation_id": str(payload.conversation_id),
            "channel": payload.channel,
            "confirmed": payload.confirmed,
            "correlation_id": request.state.correlation_id,
            "tool_name_override": payload.tool_name,
            "tool_arguments_override": payload.tool_arguments,
            "tool_calls": 0,
        },
        config={"configurable": {"thread_id": str(payload.conversation_id)}}
    )

    tool_result = state.get("tool_result") or {}
    return ChatResponse(
        conversation_id=payload.conversation_id,
        correlation_id=request.state.correlation_id,
        status=state.get("status", "failed"),
        message=state.get("response_message", "The agent could not produce a response."),
        intent=state.get("intent", "unknown"),
        tool_name=state.get("tool_name"),
        tool_executed=bool(tool_result.get("executed", False)),
        requires_confirmation=state.get("requires_confirmation", False),
        data=tool_result.get("data"),
    )
