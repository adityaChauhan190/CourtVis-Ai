"""
Court Vision AI — API Dependencies

Phase 1: development mode auto-auth.
Phase 2+: JWT authentication — change AUTH_MODE=production.
"""
import logging
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.schemas.document import UserContext
from app.storage.local import StorageService, storage_service

settings = get_settings()
logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> UserContext:
    if credentials and credentials.credentials:
        user_id = decode_access_token(credentials.credentials)
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.is_active:
                return UserContext(id=str(user.id), email=user.email, name=user.name)

    # In development mode, auto-login with dev user so local workflows are seamless
    if settings.AUTH_MODE == "development" or settings.APP_ENV == "development" or settings.DEBUG:
        return _get_or_create_dev_user(db)

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")


def _get_or_create_dev_user(db: Session) -> UserContext:
    dev_id = settings.DEV_USER_ID
    user = db.query(User).filter(User.id == dev_id).first()
    if not user:
        user = User(id=dev_id, email=settings.DEV_USER_EMAIL, name=settings.DEV_USER_NAME)
        db.add(user)
        try:
            db.commit()
            db.refresh(user)
            logger.info(f"Dev user seeded: {user.email}")
        except Exception:
            db.rollback()
            user = db.query(User).filter(User.id == dev_id).first()
    return UserContext(id=str(user.id), email=user.email, name=user.name)


def get_storage(store: StorageService = Depends(storage_service)) -> StorageService:
    return store
