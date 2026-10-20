import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class LoanDTO(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID

    loan_number: str
    loan_type: str

    principal_amount: Decimal
    outstanding_amount: Decimal
    interest_rate: Decimal

    currency: str
    status: str

    start_date: date
    maturity_date: date | None

    created_at: datetime
    updated_at: datetime


class LoanStatusDTO(BaseModel):
    id: uuid.UUID
    loan_number: str

    status: str

    principal_amount: Decimal
    outstanding_amount: Decimal

    interest_rate: Decimal
    currency: str

    maturity_date: date | None


class LoanPaymentDTO(BaseModel):
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
