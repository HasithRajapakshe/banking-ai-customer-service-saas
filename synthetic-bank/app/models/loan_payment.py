import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class LoanPayment(Base):
    __tablename__ = "loan_payment"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    loan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    payment_number: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
    )

    installment_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(19, 4),
        nullable=False,
    )

    principal_component: Mapped[Decimal] = mapped_column(
        Numeric(19, 4),
        nullable=False,
    )

    interest_component: Mapped[Decimal] = mapped_column(
        Numeric(19, 4),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    due_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )