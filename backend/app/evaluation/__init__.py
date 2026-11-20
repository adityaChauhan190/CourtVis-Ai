"""
Court Vision AI — Evaluation Package (Phase 8+)

Future: AI output accountability, traceability, and evaluation.
Components:
- EvaluationService: score AI-generated insights
- CitationVerifier: trace claims back to source documents
- ConfidenceEstimator: calibrate confidence scores
- AccountabilityReport: human-readable audit of AI reasoning
"""
from abc import ABC, abstractmethod
from typing import Any


class EvaluationService(ABC):
    """Interface for evaluating AI-generated legal insights."""

    @abstractmethod
    async def evaluate_insight(
        self, insight: str, source_documents: list[str], case_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Return evaluation with confidence, citations, and quality scores."""
        ...
