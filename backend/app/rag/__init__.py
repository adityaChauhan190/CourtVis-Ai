"""
Court Vision AI — RAG Package (Phase 3+)

Future: Hybrid RAG pipeline.
Components:
- DocumentChunker: semantic chunking of legal documents
- EmbeddingService: LegalBERT / sentence-transformers embeddings
- VectorStore: pgvector for dense retrieval
- BM25Retriever: sparse retrieval
- Reranker: cross-encoder reranking
- RAGService: hybrid retrieval orchestration
"""
from abc import ABC, abstractmethod
from typing import Any


class EmbeddingService(ABC):
    """Interface for text embedding generation."""

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        ...


class RAGService(ABC):
    """Interface for retrieval-augmented generation."""

    @abstractmethod
    async def retrieve(self, query: str, case_id: str, top_k: int = 10) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def generate(self, query: str, context: list[dict[str, Any]]) -> str:
        ...
