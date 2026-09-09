import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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