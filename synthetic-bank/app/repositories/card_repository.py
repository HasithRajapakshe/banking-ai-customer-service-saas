import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import Card


class CardRepository:

    async def get_by_id(
        self,
        db: AsyncSession,
        card_id: uuid.UUID,
    ) -> Card | None:

        result = await db.execute(
            select(Card)
            .where(Card.id == card_id)
        )

        return result.scalar_one_or_none()

    async def block(
        self,
        db: AsyncSession,
        card_id: uuid.UUID,
    ) -> Card | None:

        result = await db.execute(
            select(Card)
            .where(Card.id == card_id)
        )

        card = result.scalar_one_or_none()

        if card is None:
            return None

        if card.status == "blocked":
            return card

        if card.status != "active":
            return card

        card.status = "blocked"
        card.blocked_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(card)

        return card