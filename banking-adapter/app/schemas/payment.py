import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class PaymentDTO(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID

    source_account_id: uuid.UUID
    beneficiary_id: uuid.UUID

    payment_number: str

    amount: Decimal
    currency: str

    payment_reference: str | None
    status: str

    idempotency_key: str | None

    requested_at: datetime
    completed_at: datetime | None

    created_at: datetime
    updated_at: datetime


class PaymentStatusDTO(BaseModel):
    id: uuid.UUID
    payment_number: str
    status: str

    amount: Decimal
    currency: str

    requested_at: datetime
    completed_at: datetime | None