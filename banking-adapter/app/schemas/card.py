import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class CardDTO(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID

    card_last4: str
    card_type: str

    expiry_month: int
    expiry_year: int

    status: str
    daily_limit: Decimal | None

    issued_at: datetime
    blocked_at: datetime | None

    created_at: datetime
    updated_at: datetime


class CardTransactionDTO(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    card_id: uuid.UUID

    transaction_number: str

    amount: Decimal
    currency: str

    merchant_name: str | None
    merchant_category: str | None

    status: str

    transaction_at: datetime
    created_at: datetime