"""Court Vision AI — Case Service"""
import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.case import Case, CaseStatus
from app.models.audit import AuditLog, AuditAction
from app.schemas.case import CaseCreate, CaseUpdate

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CaseService:
    def __init__(self, db: Session):
        self.db = db

    def create_case(self, user_id: str, data: CaseCreate) -> Case:
        case = Case(
            owner_id=user_id, name=data.name, case_type=data.case_type,
            description=data.description, case_number=data.case_number,
            user_role=data.user_role, status=CaseStatus.PREPARING,
        )
        self.db.add(case)
        self.db.flush()
        self.db.add(AuditLog(
            user_id=user_id, case_id=case.id, action=AuditAction.CASE_CREATED,
            log_metadata={"name": data.name, "type": data.case_type},
        ))
        self.db.commit()
        self.db.refresh(case)
        logger.info(f"Case {case.id} created: {case.name!r}")
        return case

    def get_case(self, case_id: str, user_id: str) -> Case:
        case = self.db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found.")
        if case.owner_id == user_id:
            return case

        # Allow dev user or local development to view all cases
        if user_id == "00000000-0000-0000-0000-000000000001" or settings.APP_ENV == "development" or settings.DEBUG:
            return case

        # Check membership
        from app.models.case import CaseMember
        is_member = self.db.query(CaseMember).filter(
            CaseMember.case_id == case_id, CaseMember.user_id == user_id
        ).first()
        if is_member:
            return case

        # Allow seeded/demo cases to be viewed by all users
        if case.owner_id == "00000000-0000-0000-0000-000000000001":
            return case

        raise HTTPException(status_code=403, detail="Not authorized to access this case.")

    def list_cases(self, user_id: str) -> list[Case]:
        if user_id == "00000000-0000-0000-0000-000000000001" or settings.APP_ENV == "development" or settings.DEBUG:
            return self.db.query(Case).order_by(Case.updated_at.desc()).all()
        from sqlalchemy import or_
        from app.models.case import CaseMember
        member_case_ids = [
            m.case_id for m in self.db.query(CaseMember.case_id).filter(CaseMember.user_id == user_id).all()
        ]
        return (
            self.db.query(Case)
            .filter(
                or_(
                    Case.owner_id == user_id,
                    Case.owner_id == "00000000-0000-0000-0000-000000000001",
                    Case.id.in_(member_case_ids) if member_case_ids else False,
                )
            )
            .order_by(Case.updated_at.desc())
            .all()
        )

    def update_case(self, case_id: str, user_id: str, data: CaseUpdate) -> Case:
        case = self.get_case(case_id, user_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(case, field, value)
        self.db.add(AuditLog(user_id=user_id, case_id=case.id, action=AuditAction.CASE_UPDATED))
        self.db.commit()
        self.db.refresh(case)
        return case

    def delete_case(self, case_id: str, user_id: str) -> None:
        case = self.get_case(case_id, user_id)
        self.db.add(AuditLog(
            user_id=user_id, case_id=case.id, action=AuditAction.CASE_DELETED,
            log_metadata={"name": case.name},
        ))
        self.db.delete(case)
        self.db.commit()
