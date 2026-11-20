"""Court Vision AI — Documents API Routes"""
from fastapi import APIRouter, Depends, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_storage
from app.schemas.document import DocumentOut, DocumentStatusOut, DocumentListOut, UserContext
from app.services.document_service import DocumentService
from app.services.case_service import CaseService
from app.storage.local import StorageService

router = APIRouter(tags=["Documents"])


@router.post("/cases/{case_id}/documents", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    case_id: str, file: UploadFile = File(...),
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db), store: StorageService = Depends(get_storage),
):
    CaseService(db).get_case(case_id=case_id, user_id=current_user.id)
    doc = await DocumentService(db=db, store=store).upload_document(
        case_id=case_id, user_id=current_user.id, file=file
    )
    return DocumentOut.model_validate(doc)


@router.get("/cases/{case_id}/documents", response_model=DocumentListOut)
def list_case_documents(
    case_id: str, current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db), store: StorageService = Depends(get_storage),
):
    CaseService(db).get_case(case_id=case_id, user_id=current_user.id)
    docs = DocumentService(db=db, store=store).get_case_documents(case_id=case_id)
    return DocumentListOut(documents=[DocumentOut.model_validate(d) for d in docs], total=len(docs))


@router.get("/documents/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: str, current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db), store: StorageService = Depends(get_storage),
):
    doc = DocumentService(db=db, store=store).get_document(document_id=document_id, user_id=current_user.id)
    return DocumentOut.model_validate(doc)


@router.get("/documents/{document_id}/status", response_model=DocumentStatusOut)
def get_document_status(
    document_id: str, current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db), store: StorageService = Depends(get_storage),
):
    doc = DocumentService(db=db, store=store).get_document(document_id=document_id, user_id=current_user.id)
    return DocumentStatusOut.model_validate(doc)


@router.get("/documents/{document_id}/file")
def serve_document(
    document_id: str, current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db), store: StorageService = Depends(get_storage),
):
    """Serve the raw PDF — protected, no public URLs."""
    doc = DocumentService(db=db, store=store).get_document(document_id=document_id, user_id=current_user.id)
    local_path = store.get_local_path(doc.storage_path)
    return FileResponse(path=local_path, media_type="application/pdf", filename=doc.original_name)


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str, current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db), store: StorageService = Depends(get_storage),
):
    DocumentService(db=db, store=store).delete_document(document_id=document_id, user_id=current_user.id)
