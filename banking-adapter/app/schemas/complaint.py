import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


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


class ComplaintDTO(BaseModel):
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


class ComplaintStatusDTO(BaseModel):
    id: uuid.UUID
    complaint_number: str

    status: ComplaintStatus
    priority: ComplaintPriority

    assigned_to: uuid.UUID | None
    resolved_at: datetime | None

    updated_at: datetime
