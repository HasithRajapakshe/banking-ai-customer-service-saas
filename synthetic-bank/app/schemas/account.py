import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    account_number: str
    account_type: str
    currency: str
    current_balance: Decimal
    available_balance: Decimal
    status: str
    opened_at: datetime
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AccountBalanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: uuid.UUID
    account_number: str
    currency: str
    current_balance: Decimal
    available_balance: Decimal