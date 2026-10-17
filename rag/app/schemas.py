import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    document_key: str
    title: str
    document_type: str
    status: str
    created_at: datetime
    updated_at: datetime


class DocumentUploadResponse(BaseModel):
    success: bool
    document_id: uuid.UUID
    document_version_id: uuid.UUID
    chunk_count: int
