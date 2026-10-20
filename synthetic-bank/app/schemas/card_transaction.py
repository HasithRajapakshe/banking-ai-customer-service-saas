import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CardTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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