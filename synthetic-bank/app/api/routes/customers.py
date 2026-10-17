import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db

from app.core.customer_context import require_customer_context
from app.schemas.customer import CustomerResponse
from app.schemas.account import AccountResponse
from app.schemas.card import CardResponse
from app.services.customer_service import CustomerService
from app.services.account_service import AccountService
from app.services.card_service import CardService


router = APIRouter(
    prefix="/api/v1/customers",
    tags=["Customers"],
)

customer_service = CustomerService()
account_service = AccountService()
card_service = CardService()


# =========================
# Get Customer
# =========================

@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
    dependencies=[
        Depends(require_customer_context),
    ],
)
async def get_customer(
    customer_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    trusted_customer_id = request.state.customer_id

    # Prevent Customer A from requesting Customer B
    if customer_id != trusted_customer_id:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    return await customer_service.get_customer(
        db,
        trusted_customer_id,
    )


# =========================
# Get Customer Accounts
# =========================

@router.get(
    "/{customer_id}/accounts",
    response_model=list[AccountResponse],
    dependencies=[
        Depends(require_customer_context),
    ],
)
async def get_customer_accounts(
    customer_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    trusted_customer_id = request.state.customer_id
    tenant_id = request.state.tenant_id

    # Prevent Customer A from requesting Customer B's accounts
    if customer_id != trusted_customer_id:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    return await account_service.get_accounts_by_customer(
        db,
        trusted_customer_id,
        tenant_id,
    )


# =========================
# Get Customer Cards
# =========================

@router.get(
    "/{customer_id}/cards",
    response_model=list[CardResponse],
    dependencies=[
        Depends(require_customer_context),
    ],
)
async def get_customer_cards(
    customer_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    trusted_customer_id = request.state.customer_id
    tenant_id = request.state.tenant_id

    # Prevent Customer A from requesting Customer B's cards
    if customer_id != trusted_customer_id:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    return await card_service.get_cards_by_customer(
        db,
        trusted_customer_id,
        tenant_id,
    )