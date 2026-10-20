import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class LoanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


class LoanStatusResponse(BaseModel):
    id: uuid.UUID
    loan_number: str

    status: str

    principal_amount: Decimal
    outstanding_amount: Decimal

    interest_rate: Decimal
    currency: str

    maturity_date: date | None