"""Court Vision AI — Celery Tasks"""
import logging
import time
from datetime import datetime, timezone
from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.document import Document, DocumentProcessingJob, DocumentStatus, ProcessingJobStatus
from app.storage.local import StorageService, storage_service
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

@celery_app.task(name="process_document_task")
def process_document_task(document_id: str, job_id: str):
    logger.info(f"Starting processing for document {document_id}, job {job_id}")
    
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        job = db.query(DocumentProcessingJob).filter(DocumentProcessingJob.id == job_id).first()
        
        if not doc or not job:
            logger.error("Document or Job not found in DB.")
            return

        job.status = ProcessingJobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        # Extract page count via PyMuPDF
        store = storage_service()
        local_path = store.get_local_path(doc.storage_path)
        
        page_count = None
        try:
            import fitz
            pdf_doc = fitz.open(local_path)
            page_count = len(pdf_doc)
            pdf_doc.close()
        except Exception as e:
            logger.warning(f"Page count extraction failed: {e}")
            job.status = ProcessingJobStatus.FAILED
            job.error_message = f"Failed to open PDF: {str(e)}"
            doc.status = DocumentStatus.FAILED
            doc.error_message = "Corrupted or invalid PDF file."
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
            return
            
        # Simulate some NLP / RAG processing delay for now (Phase 3 will add real logic)
        time.sleep(2)

        # Update Document and Job on success
        doc.page_count = page_count
        doc.status = DocumentStatus.READY
        doc.processed_at = datetime.now(timezone.utc)
        
        job.status = ProcessingJobStatus.COMPLETED
        job.completed_at = datetime.now(timezone.utc)
        
        db.commit()
        logger.info(f"Successfully processed document {document_id}")

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        db.rollback()
        # Attempt to mark as failed
        try:
            job = db.query(DocumentProcessingJob).filter(DocumentProcessingJob.id == job_id).first()
            doc = db.query(Document).filter(Document.id == document_id).first()
            if job:
                job.status = ProcessingJobStatus.FAILED
                job.error_message = str(e)
                job.completed_at = datetime.now(timezone.utc)
            if doc:
                doc.status = DocumentStatus.FAILED
                doc.error_message = "Internal processing error."
            db.commit()
        except Exception:
            pass
    finally:
        db.close()
