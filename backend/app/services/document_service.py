"""Court Vision AI — Document Service"""
import uuid
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.document import Document, DocumentStatus, DocumentProcessingJob, ProcessingJobStatus
from app.models.audit import AuditLog, AuditAction
from app.storage.local import StorageService, storage_service

settings = get_settings()
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf"}
PDF_MAGIC_BYTES = b"%PDF"


def _process_document_sync(document_id: str, job_id: str) -> None:
    """
    Process a document in a background thread — no Celery/Redis needed.
    Opens its own DB session so it is fully independent of the request session.
    """
    logger.info(f"[BG] Processing document {document_id}, job {job_id}")
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        job = db.query(DocumentProcessingJob).filter(DocumentProcessingJob.id == job_id).first()

        if not doc or not job:
            logger.error(f"[BG] Document or Job not found: doc={document_id}, job={job_id}")
            return

        job.status = ProcessingJobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        store = storage_service()
        local_path = store.get_local_path(doc.storage_path)

        page_count = None
        try:
            import fitz  # PyMuPDF
            pdf_doc = fitz.open(local_path)
            page_count = len(pdf_doc)
            pdf_doc.close()
            logger.info(f"[BG] PDF opened OK: {page_count} pages — {doc.original_name}")
        except Exception as e:
            logger.error(f"[BG] PDF open failed for {local_path}: {e}")
            job.status = ProcessingJobStatus.FAILED
            job.error_message = f"Failed to open PDF: {e}"
            job.completed_at = datetime.now(timezone.utc)
            doc.status = DocumentStatus.FAILED
            doc.error_message = "Corrupted or invalid PDF file."
            db.commit()
            return

        # Mark document READY
        doc.page_count = page_count
        doc.status = DocumentStatus.READY
        doc.processed_at = datetime.now(timezone.utc)
        job.status = ProcessingJobStatus.COMPLETED
        job.completed_at = datetime.now(timezone.utc)
        # The case's documents changed → its cached evidence graph is stale
        from app.models.case import Case
        case = db.query(Case).filter(Case.id == doc.case_id).first()
        if case:
            case.evidence_graph = None
        db.commit()
        logger.info(f"[BG] Document {document_id} is now READY ({page_count} pages)")

        # Add the document to the precedent knowledge base (non-fatal on failure)
        try:
            from app.services.precedent_service import index_document
            index_document(db, doc, store)
        except Exception as e:
            db.rollback()
            logger.warning(f"[BG] Precedent indexing failed for {document_id}: {e}")

    except Exception as e:
        logger.error(f"[BG] Unexpected error processing {document_id}: {e}", exc_info=True)
        db.rollback()
        try:
            doc = db.query(Document).filter(Document.id == document_id).first()
            job = db.query(DocumentProcessingJob).filter(DocumentProcessingJob.id == job_id).first()
            if doc:
                doc.status = DocumentStatus.FAILED
                doc.error_message = "Internal processing error."
            if job:
                job.status = ProcessingJobStatus.FAILED
                job.error_message = str(e)
                job.completed_at = datetime.now(timezone.utc)
            db.commit()
        except Exception:
            pass
    finally:
        db.close()


class DocumentService:
    def __init__(self, db: Session, store: StorageService):
        self.db = db
        self.store = store

    async def _validate_file(self, file: UploadFile) -> bytes:
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Only PDF files are accepted. Received: {suffix or 'unknown extension'}",
            )
        content = await file.read()
        if len(content) > settings.max_upload_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds the maximum size of {settings.MAX_UPLOAD_SIZE_MB}MB.",
            )
        if not content.startswith(PDF_MAGIC_BYTES):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="File does not appear to be a valid PDF (magic byte check failed).",
            )
        import io
        file.file = io.BytesIO(content)
        file.size = len(content)
        return content



    async def upload_document(self, case_id: str, user_id: str, file: UploadFile) -> Document:
        await self._validate_file(file)

        stored_filename = f"{uuid.uuid4()}.pdf"
        destination = f"{case_id}/{stored_filename}"

        doc = Document(
            case_id=case_id, uploader_id=user_id,
            original_name=file.filename or stored_filename,
            stored_filename=stored_filename, mime_type="application/pdf",
            file_size=file.size or 0, storage_path=destination,
            status=DocumentStatus.UPLOADING,
        )
        self.db.add(doc)
        self.db.flush()

        try:
            storage_path = await self.store.upload(file, destination)
            doc.storage_path = storage_path
            doc.status = DocumentStatus.PROCESSING
        except Exception as e:
            logger.error(f"Storage upload failed: {e}")
            doc.status = DocumentStatus.FAILED
            doc.error_message = "File upload failed."
            self.db.commit()
            raise HTTPException(status_code=500, detail="Document upload failed.")

        job = DocumentProcessingJob(
            document_id=doc.id, status=ProcessingJobStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(job)
        self.db.flush()

        self.db.add(AuditLog(
            user_id=user_id, case_id=case_id, document_id=doc.id,
            action=AuditAction.DOCUMENT_UPLOADED,
            log_metadata={"filename": doc.original_name, "file_size": doc.file_size},
        ))

        # IMPORTANT: Commit BEFORE starting the background thread so the
        # thread's independent session can actually find the document row.
        doc_id = doc.id
        job_id = job.id
        self.db.commit()
        self.db.refresh(doc)

        # Run document processing in a background thread
        threading.Thread(
            target=_process_document_sync,
            args=(doc_id, job_id),
            daemon=True,
        ).start()

        logger.info(f"Document {doc.id} uploaded: {doc.original_name}. Processing started in background.")
        return doc

    def get_document(self, document_id: str, user_id: str) -> Document:
        doc = self.db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found.")
        return doc

    def get_case_documents(self, case_id: str) -> list[Document]:
        return (
            self.db.query(Document).filter(Document.case_id == case_id)
            .order_by(Document.uploaded_at.desc()).all()
        )

    def delete_document(self, document_id: str, user_id: str) -> None:
        doc = self.get_document(document_id, user_id)
        # Synchronous file deletion (avoids asyncio.run complexity in sync context)
        try:
            local_path = self.store.get_local_path(doc.storage_path)
            import os
            if os.path.exists(local_path):
                os.unlink(local_path)
        except Exception as e:
            logger.warning(f"File delete failed for {doc.storage_path}: {e}")

        self.db.add(AuditLog(
            user_id=user_id, case_id=doc.case_id, document_id=doc.id,
            action=AuditAction.DOCUMENT_DELETED,
            log_metadata={"filename": doc.original_name},
        ))
        from app.models.case import Case
        case = self.db.query(Case).filter(Case.id == doc.case_id).first()
        if case:
            case.evidence_graph = None  # graph cache is stale once a document is removed
        # The precedent library keeps its copy (source_document_id is set to NULL by the FK)
        self.db.delete(doc)
        self.db.commit()
        logger.info(f"Document {document_id} deleted")
