"""
Court Vision AI — Workers Package (Phase 2+)

Future: Celery task queue for async document processing,
NLP analysis, embedding generation, graph indexing.
"""
from .celery_app import celery_app

__all__ = ["celery_app"]
