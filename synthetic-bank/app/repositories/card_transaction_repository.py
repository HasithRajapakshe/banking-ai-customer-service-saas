import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card_transaction import CardTransaction


class CardTransactionRepository:

    async def get_by_card_id(
        self,
        db: AsyncSession,
        card_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[CardTransaction]:

        result = await db.execute(
            select(CardTransaction)
            .where(
                CardTransaction.card_id == card_id
            )
            .order_by(
                CardTransaction.transaction_at.desc(),
                CardTransaction.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        return list(result.scalars().all())