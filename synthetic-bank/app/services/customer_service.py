import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.customer_repository import CustomerRepository


class CustomerService:

    def __init__(self):
        self.repository = CustomerRepository()

    async def get_customer(
        self,
        db: AsyncSession,
        customer_id: uuid.UUID,
    ):
        customer = await self.repository.get_by_id(
            db,
            customer_id,
        )

        if customer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        return customer
