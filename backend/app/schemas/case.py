"""
Court Vision AI — Pydantic Schemas: Case
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.case import CaseType, CaseStatus, UserCaseRole


class CaseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    case_type: CaseType
    description: Optional[str] = Field(None, max_length=5000)
    case_number: Optional[str] = Field(None, max_length=100)
    user_role: UserCaseRole = UserCaseRole.RESEARCHER


class CaseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    status: Optional[CaseStatus] = None


class CaseOut(BaseModel):
    id: str
    name: str
    case_type: CaseType
    description: Optional[str]
    case_number: Optional[str]
    user_role: UserCaseRole
    status: CaseStatus
    owner_id: str
    document_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CaseListOut(BaseModel):
    cases: list[CaseOut]
    total: int
