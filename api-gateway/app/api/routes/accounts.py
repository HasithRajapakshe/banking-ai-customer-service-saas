import httpx
from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.dependencies import get_current_active_user
from app.core.config import settings
from app.models import AppUser

router = APIRouter(prefix="/api/v1/accounts", tags=["Accounts"])


async def proxy_request(request: Request, current_user: AppUser, method: str, path: str, params: dict = None):
    if not current_user.customer_id:
        raise HTTPException(status_code=403, detail="User is not a customer")

    correlation_id = getattr(request.state, "correlation_id", "req-123")
    if path == "":
        url = f"{settings.synthetic_bank_base_url}/api/v1/customers/{current_user.customer_id}/accounts"
    else:
        url = f"{settings.synthetic_bank_base_url}/api/v1/accounts{path}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method,
                url,
                params=params,
                headers={
                    "X-Correlation-ID": correlation_id,
                    "X-Tenant-ID": str(current_user.tenant_id),
                    "X-Customer-ID": str(current_user.customer_id),
                    "X-Internal-API-Key": settings.synthetic_bank_api_key,
                },
                timeout=10.0
            )
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Resource not found")
            if response.status_code == 403:
                raise HTTPException(status_code=403, detail="Forbidden")
            response.raise_for_status()
            return response.json()
        except HTTPException:
            raise
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (404, 403):
                raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
            import logging
            logging.error(f"Failed to fetch accounts from synthetic-bank: {exc.response.text}")
            raise HTTPException(status_code=500, detail="Internal server error")
        except Exception as exc:
            import logging
            logging.error("Failed to fetch accounts: %s", exc)
            raise HTTPException(status_code=500, detail="Internal server error")


@router.get("")
async def list_accounts(
    request: Request,
    current_user: AppUser = Depends(get_current_active_user),
):
    """Proxy to Synthetic Bank to list accounts for the current customer."""
    if not current_user.customer_id:
        return []
    return await proxy_request(request, current_user, "GET", "")


@router.get("/{account_id}")
async def get_account(
    account_id: str,
    request: Request,
    current_user: AppUser = Depends(get_current_active_user),
):
    return await proxy_request(request, current_user, "GET", f"/{account_id}")


@router.get("/{account_id}/transactions")
async def get_account_transactions(
    account_id: str,
    request: Request,
    current_user: AppUser = Depends(get_current_active_user),
    limit: int = 20,
    offset: int = 0,
):
    return await proxy_request(
        request, 
        current_user, 
        "GET", 
        f"/{account_id}/transactions",
        params={"limit": limit, "offset": offset}
    )
