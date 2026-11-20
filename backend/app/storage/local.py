"""
Court Vision AI — Storage Service Abstraction

Defines the StorageService interface and provides a local filesystem
implementation for development. Swap implementation to S3StorageService
for production without changing any service-layer code.
"""
import os
import uuid
import shutil
import aiofiles
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO
from fastapi import UploadFile
from app.core.config import get_settings

settings = get_settings()


class StorageService(ABC):
    """Abstract storage service. Implement for local, S3, GCS, etc."""

    @abstractmethod
    async def upload(self, file: UploadFile, destination: str) -> str:
        """Upload a file and return the storage path."""
        ...

    @abstractmethod
    async def download(self, storage_path: str) -> bytes:
        """Download a file by storage path and return bytes."""
        ...

    @abstractmethod
    async def delete(self, storage_path: str) -> None:
        """Delete a file from storage."""
        ...

    @abstractmethod
    def get_local_path(self, storage_path: str) -> str:
        """Return the local filesystem path for serving/streaming."""
        ...


class LocalStorageService(StorageService):
    """
    Local filesystem implementation of StorageService.
    Documents are stored under LOCAL_STORAGE_PATH/{case_id}/{filename}.
    This is NOT publicly accessible — files are served through protected API endpoints.
    """

    def __init__(self):
        self.base_path = Path(settings.LOCAL_STORAGE_PATH).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _case_dir(self, case_id: str) -> Path:
        """Return the directory for a specific case, creating it if needed."""
        p = self.base_path / str(case_id)
        p.mkdir(parents=True, exist_ok=True)
        return p

    async def upload(self, file: UploadFile, destination: str) -> str:
        """
        Write UploadFile to disk.
        destination format: "{case_id}/{stored_filename}"
        Returns the storage path (relative to base_path).
        """
        parts = destination.split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid destination format: {destination!r}")
        case_id, filename = parts
        target = self._case_dir(case_id) / filename

        async with aiofiles.open(target, "wb") as f:
            while chunk := await file.read(1024 * 1024):  # 1 MB chunks
                await f.write(chunk)

        return str(target.relative_to(self.base_path))

    async def download(self, storage_path: str) -> bytes:
        """Read file from disk and return bytes."""
        target = self.base_path / storage_path
        if not target.exists():
            raise FileNotFoundError(f"File not found: {storage_path}")
        async with aiofiles.open(target, "rb") as f:
            return await f.read()

    async def delete(self, storage_path: str) -> None:
        """Remove file from disk."""
        target = self.base_path / storage_path
        if target.exists():
            target.unlink()

    def get_local_path(self, storage_path: str) -> str:
        return str(self.base_path / storage_path)


def get_storage_service() -> StorageService:
    """
    Factory function — returns the configured storage backend.
    Switch STORAGE_BACKEND env var to 's3' to use S3StorageService in future.
    """
    if settings.STORAGE_BACKEND == "local":
        return LocalStorageService()
    # Future: elif settings.STORAGE_BACKEND == "s3": return S3StorageService()
    raise ValueError(f"Unsupported storage backend: {settings.STORAGE_BACKEND}")


# Singleton instance
_storage_service: StorageService | None = None


def storage_service() -> StorageService:
    """Dependency-injectable storage service singleton."""
    global _storage_service
    if _storage_service is None:
        _storage_service = get_storage_service()
    return _storage_service
