"""
Court Vision AI — Pydantic Schemas: Document
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.document import DocumentStatus


class DocumentOut(BaseModel):
    id: str
    case_id: str
    original_name: str
    mime_type: str
    file_size: int
    page_count: Optional[int]
    status: DocumentStatus
    error_message: Optional[str]
    uploaded_at: datetime
    processed_at: Optional[datetime]
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentStatusOut(BaseModel):
    id: str
    status: DocumentStatus
    page_count: Optional[int]
    error_message: Optional[str]
    processed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class DocumentListOut(BaseModel):
    documents: list[DocumentOut]
    total: int


class UserContext(BaseModel):
    """Authenticated user context passed through request state."""
    id: str
    email: str
    name: str
