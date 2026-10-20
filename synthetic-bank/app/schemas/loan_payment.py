import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class LoanPaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    loan_id: uuid.UUID

    payment_number: str
    installment_number: int

    amount: Decimal
    principal_component: Decimal
    interest_component: Decimal

    currency: str

    due_date: date
    paid_at: datetime | None

    status: str
    created_at: datetime