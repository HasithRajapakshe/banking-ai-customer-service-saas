import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import Card


class CardRepository:

    async def get_by_id(
        self,
        db: AsyncSession,
        card_id: uuid.UUID,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
    ) -> Card | None:

        result = await db.execute(
            select(Card).where(
                Card.id == card_id,
                Card.tenant_id == tenant_id,
                Card.customer_id == customer_id,
            )
        )

        return result.scalar_one_or_none()

    async def block(
        self,
        db: AsyncSession,
        card: Card,
    ) -> Card:

        card.status = "blocked"

        await db.commit()
        await db.refresh(card)

        return card