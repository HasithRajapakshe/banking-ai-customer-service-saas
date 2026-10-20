"""Accounts for the dashboard, read through the Tool Gateway (not the bank directly)."""

import uuid

from fastapi import APIRouter, Depends, Query, Request

from app.api.dependencies import get_current_active_user, get_current_user_roles
from app.core.internal_token import sign_internal_token
from app.models import AppUser, Role
from app.services.tool_gateway_client import tool_gateway_client

router = APIRouter(prefix="/api/v1/accounts", tags=["Accounts"])


def _correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", None) or str(uuid.uuid4())


async def _run(request: Request, user: AppUser, roles: list[Role], tool: str, arguments: dict):
    token = sign_internal_token(user, [r.role_code for r in roles])
    return await tool_gateway_client.run(tool, arguments, token=token, correlation_id=_correlation_id(request))


@router.get("")
async def list_accounts(
    request: Request,
    current_user: AppUser = Depends(get_current_active_user),
    roles: list[Role] = Depends(get_current_user_roles),
):
    """The current customer's accounts (account.list)."""
    if not current_user.customer_id:
        return []
    return await _run(request, current_user, roles, "account.list", {"limit": 100, "offset": 0})


@router.get("/{account_id}")
async def get_account(
    account_id: uuid.UUID,
    request: Request,
    current_user: AppUser = Depends(get_current_active_user),
    roles: list[Role] = Depends(get_current_user_roles),
):
    return await _run(request, current_user, roles, "account.get_details", {"account_id": str(account_id)})


@router.get("/{account_id}/transactions")
async def get_account_transactions(
    account_id: uuid.UUID,
    request: Request,
    current_user: AppUser = Depends(get_current_active_user),
    roles: list[Role] = Depends(get_current_user_roles),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return await _run(
        request, current_user, roles, "account.get_transactions",
        {"account_id": str(account_id), "limit": limit, "offset": offset},
    )
