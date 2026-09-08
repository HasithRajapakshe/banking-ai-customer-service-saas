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
    ):
        return await self.repository.get_by_id(
            db,
            card_id,
        )

    async def block_card(
        self,
        db: AsyncSession,
        card_id: uuid.UUID,
    ):
        return await self.repository.block(
            db,
            card_id,
        )