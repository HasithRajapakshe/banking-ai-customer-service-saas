import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ComplaintPriority = Literal[
    "low",
    "medium",
    "high",
    "critical",
]

ComplaintStatus = Literal[
    "open",
    "in_progress",
    "waiting_customer",
    "resolved",
    "closed",
]


class ComplaintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID

    complaint_number: str

    category: str
    priority: ComplaintPriority

    subject: str
    description: str

    status: ComplaintStatus

    assigned_to: uuid.UUID | None
    resolved_at: datetime | None

    created_at: datetime
    updated_at: datetime


class ComplaintCreateRequest(BaseModel):
    category: str = Field(
        min_length=2,
        max_length=50,
    )

    priority: ComplaintPriority = "medium"

    subject: str = Field(
        min_length=3,
        max_length=255,
    )

    description: str = Field(
        min_length=5,
        max_length=5000,
    )


class ComplaintStatusResponse(BaseModel):
    id: uuid.UUID
    complaint_number: str

    status: ComplaintStatus
    priority: ComplaintPriority

    assigned_to: uuid.UUID | None
    resolved_at: datetime | None

    updated_at: datetime