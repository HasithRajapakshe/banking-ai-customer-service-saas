import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.card_transaction_repository import (
    CardTransactionRepository,
)


class CardTransactionService:

    def __init__(self):
        self.repository = CardTransactionRepository()

    async def get_card_transactions(
        self,
        db: AsyncSession,
        card_id: uuid.UUID,
        tenant_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ):
        return await self.repository.get_by_card_id(
            db,
            card_id,
            tenant_id,
            limit,
            offset,
        )