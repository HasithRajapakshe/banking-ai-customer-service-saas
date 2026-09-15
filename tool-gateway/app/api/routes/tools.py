from fastapi import APIRouter, Request

from app.schemas.context import ToolExecutionContext
from app.schemas.tool import ToolExecutionRequest
from app.services.tool_gateway_service import (
    tool_gateway_service,
)
from app.tools.registry import tool_registry


router = APIRouter(
    prefix="/api/v1/tools",
    tags=["Tools"],
)


@router.get("")
async def list_tools():
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "risk_level": tool.risk_level,
            "requires_confirmation": tool.requires_confirmation,
            "permission": tool.permission,
        }
        for tool in tool_registry.all()
    ]


@router.get("/{tool_name:path}")
async def get_tool(tool_name: str):
    tool = tool_registry.get(tool_name)

    if tool is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail={
                "code": "TOOL_NOT_FOUND",
                "message": f"Unknown tool: {tool_name}",
            },
        )

    return {
        "name": tool.name,
        "description": tool.description,
        "risk_level": tool.risk_level,
        "requires_confirmation": tool.requires_confirmation,
        "permission": tool.permission,
    }


@router.post("/execute")
async def execute_tool(
    payload: ToolExecutionRequest,
    request: Request,
):
    context = ToolExecutionContext(
        tenant_id=payload.tenant_id,
        customer_id=payload.customer_id,
        user_id=payload.user_id,
        conversation_id=payload.conversation_id,
        correlation_id=request.state.correlation_id,
        channel=payload.channel,
    )

    return await tool_gateway_service.execute(
        tool_name=payload.tool_name,
        context=context,
        arguments=payload.arguments,
        confirmed=payload.confirmed,
    )