import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Card(Base):
    __tablename__ = "card"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    card_number_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    card_last4: Mapped[str] = mapped_column(
        String(4),
        nullable=False,
    )

    card_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    expiry_month: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )

    expiry_year: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    daily_limit: Mapped[Decimal | None] = mapped_column(
        Numeric(19, 4),
        nullable=True,
    )

    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    blocked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )