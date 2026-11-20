"""Court Vision AI — Cases API Routes"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.api.deps import get_current_user, get_db
from app.schemas.case import CaseCreate, CaseOut, CaseListOut
from app.schemas.document import UserContext
from app.services.case_service import CaseService
from app.models.document import Document
from app.models.case import CaseStatus

router = APIRouter(prefix="/cases", tags=["Cases"])


def _enrich_case(case, db: Session) -> CaseOut:
    doc_count = db.query(Document).filter(Document.case_id == case.id).count()
    return CaseOut(
        id=case.id, name=case.name, case_type=case.case_type,
        description=case.description, case_number=case.case_number,
        user_role=case.user_role, status=case.status, owner_id=case.owner_id,
        document_count=doc_count, created_at=case.created_at, updated_at=case.updated_at,
    )


@router.post("", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
def create_case(data: CaseCreate, current_user: UserContext = Depends(get_current_user), db: Session = Depends(get_db)):
    case = CaseService(db).create_case(user_id=current_user.id, data=data)
    return _enrich_case(case, db)


@router.get("", response_model=CaseListOut)
def list_cases(current_user: UserContext = Depends(get_current_user), db: Session = Depends(get_db)):
    cases = CaseService(db).list_cases(user_id=current_user.id)
    return CaseListOut(cases=[_enrich_case(c, db) for c in cases], total=len(cases))


@router.get("/{case_id}", response_model=CaseOut)
def get_case(case_id: str, current_user: UserContext = Depends(get_current_user), db: Session = Depends(get_db)):
    case = CaseService(db).get_case(case_id=case_id, user_id=current_user.id)
    return _enrich_case(case, db)


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(case_id: str, current_user: UserContext = Depends(get_current_user), db: Session = Depends(get_db)):
    CaseService(db).delete_case(case_id=case_id, user_id=current_user.id)


class CaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    case_number: Optional[str] = None
    status: Optional[CaseStatus] = None


@router.patch("/{case_id}", response_model=CaseOut)
def update_case(
    case_id: str,
    data: CaseUpdate,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Partially update a case's editable fields."""
    case = CaseService(db).get_case(case_id=case_id, user_id=current_user.id)
    if data.name is not None:
        case.name = data.name
    if data.description is not None:
        case.description = data.description
    if data.case_number is not None:
        case.case_number = data.case_number
    if data.status is not None:
        case.status = data.status
    db.commit()
    db.refresh(case)
    return _enrich_case(case, db)
