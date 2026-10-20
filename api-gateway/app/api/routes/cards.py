"""Cards for the dashboard ("My cards"), read through the Tool Gateway."""

import uuid

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import get_current_active_user, get_current_user_roles
from app.core.internal_token import sign_internal_token
from app.models import AppUser, Role
from app.services.tool_gateway_client import tool_gateway_client

router = APIRouter(prefix="/api/v1/cards", tags=["Cards"])


@router.get("")
async def list_cards(
    request: Request,
    current_user: AppUser = Depends(get_current_active_user),
    roles: list[Role] = Depends(get_current_user_roles),
):
    """The current customer's cards (card.list): id, type, last 4 digits, status."""
    if not current_user.customer_id:
        return []
    token = sign_internal_token(current_user, [r.role_code for r in roles])
    correlation_id = getattr(request.state, "correlation_id", None) or str(uuid.uuid4())
    return await tool_gateway_client.run("card.list", {}, token=token, correlation_id=correlation_id)
