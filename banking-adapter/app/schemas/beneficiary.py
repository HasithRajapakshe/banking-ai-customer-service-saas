import uuid
from datetime import datetime

from pydantic import BaseModel


class BeneficiaryDTO(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID

    beneficiary_number: str
    beneficiary_name: str

    bank_name: str | None
    account_number_masked: str | None

    status: str

    created_at: datetime
    updated_at: datetime
