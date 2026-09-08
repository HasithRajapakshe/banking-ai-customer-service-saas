import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db
from app.schemas.customer import CustomerResponse
from app.schemas.account import AccountResponse
from app.services.customer_service import CustomerService
from app.services.account_service import AccountService


router = APIRouter(
    prefix="/api/v1/customers",
    tags=["Customers"],
)

customer_service = CustomerService()
account_service = AccountService()


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
)
async def get_customer(
    customer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await customer_service.get_customer(
        db,
        customer_id,
    )


@router.get(
    "/{customer_id}/accounts",
    response_model=list[AccountResponse],
)
async def get_customer_accounts(
    customer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await account_service.get_accounts_by_customer(
        db,
        customer_id,
    )