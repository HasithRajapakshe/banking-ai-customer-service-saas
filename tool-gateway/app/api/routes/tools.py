from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app.core.internal_auth import InternalIdentity, identity_mismatch, require_internal_identity
from app.schemas.context import ToolExecutionContext
from app.schemas.tool import ToolExecutionRequest
from app.services.audit_service import audit_service
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
            # JSON Schema of the arguments, so clients (the AI agent) can
            # build tool definitions without hard-coding them.
            "input_schema": tool.input_model.model_json_schema(),
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
        "input_schema": tool.input_model.model_json_schema(),
    }


@router.post("/execute")
async def execute_tool(
    payload: ToolExecutionRequest,
    request: Request,
    identity: InternalIdentity = Depends(require_internal_identity),
):
    if identity.customer_id is None:
        # Banking tools always act for a customer (admins have none).
        raise identity_mismatch("customer_id")

    context = ToolExecutionContext(
        tenant_id=identity.tenant_id,
        customer_id=identity.customer_id,
        user_id=identity.user_id,
        conversation_id=identity.conversation_id,
        correlation_id=request.state.correlation_id,
        channel=payload.channel,
        roles=identity.roles,
    )

    # Identity is taken ONLY from the verified token; the body may repeat it
    # but can never change it. The caller is authenticated, so the attempt
    # is attributable and audited as denied.
    for field in ("tenant_id", "customer_id", "user_id", "conversation_id"):
        sent = getattr(payload, field)
        if sent is not None and sent != getattr(identity, field):
            await audit_service.log_execution(
                tool_name=payload.tool_name, context=context, risk_level="LOW", executed=False,
                success=False, error_code="IDENTITY_MISMATCH",
                error_message=f"{field} {sent} does not match the token", arguments=payload.arguments,
            )
            raise identity_mismatch(field)

    result = await tool_gateway_service.execute(
        tool_name=payload.tool_name,
        context=context,
        arguments=payload.arguments,
        confirmed=payload.confirmed,
        challenge_code=payload.challenge_code,
    )
    if result.error and result.error.code == "PERMISSION_DENIED":
        return JSONResponse(status_code=403, content=result.model_dump(mode="json"))
    return result