import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BeneficiaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


class BeneficiaryCreateRequest(BaseModel):
    beneficiary_name: str = Field(
        min_length=2,
        max_length=255,
    )

    bank_name: str | None = Field(
        default=None,
        max_length=255,
    )

    account_number: str = Field(
        min_length=4,
        max_length=50,
    )
