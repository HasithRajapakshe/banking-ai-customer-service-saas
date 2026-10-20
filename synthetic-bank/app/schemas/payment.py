import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


class PaymentCreateRequest(BaseModel):
    source_account_id: uuid.UUID
    beneficiary_id: uuid.UUID

    amount: Decimal = Field(
        gt=0
    )

    currency: str = Field(
        min_length=3,
        max_length=3,
    )

    payment_reference: str | None = None

    idempotency_key: str | None = None