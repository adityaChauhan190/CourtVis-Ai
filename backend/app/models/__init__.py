"""Court Vision AI — Models package. Import all models here so Alembic can detect them."""
from app.models.user import User, UserRole
from app.models.case import Case, CaseMember, CaseType, CaseStatus, UserCaseRole
from app.models.document import Document, DocumentPage, DocumentProcessingJob, DocumentStatus, ProcessingJobStatus
from app.models.audit import AuditLog, AuditAction
from app.models.precedent import Precedent

__all__ = [
    "User", "UserRole",
    "Case", "CaseMember", "CaseType", "CaseStatus", "UserCaseRole",
    "Document", "DocumentPage", "DocumentProcessingJob", "DocumentStatus", "ProcessingJobStatus",
    "AuditLog", "AuditAction",
    "Precedent",
]
