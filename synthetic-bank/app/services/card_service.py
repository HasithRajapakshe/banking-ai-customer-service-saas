import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.card_repository import CardRepository


class CardService:

    def __init__(self):
        self.repository = CardRepository()

    async def get_card(
        self,
        db: AsyncSession,
        card_id: uuid.UUID,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
    ):
        return await self.repository.get_by_id(
            db,
            card_id,
            tenant_id,
            customer_id,
        )

    async def block_card(
        self,
        db: AsyncSession,
        card_id: uuid.UUID,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
    ):
        card = await self.repository.get_by_id(
            db,
            card_id,
            tenant_id,
            customer_id,
        )

        if card is None:
            return None

        return await self.repository.block(
            db,
            card,
        )