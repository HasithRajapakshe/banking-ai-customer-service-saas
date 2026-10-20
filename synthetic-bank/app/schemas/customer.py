import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_number: str
    first_name: str
    last_name: str
    email: str | None
    phone: str | None
    date_of_birth: date | None
    status: str
    created_at: datetime
    updated_at: datetime
