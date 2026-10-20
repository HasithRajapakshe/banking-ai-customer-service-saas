import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class AccountTransactionDTO(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    account_id: uuid.UUID

    transaction_number: str
    transaction_type: str

    amount: Decimal
    currency: str
    direction: str

    balance_after: Decimal

    description: str | None
    merchant_name: str | None

    transaction_at: datetime
    created_at: datetime