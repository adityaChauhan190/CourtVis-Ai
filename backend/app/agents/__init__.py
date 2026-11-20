"""
Court Vision AI — AI Agents Package (Phase 4+)

Future: LangGraph multi-agent architecture.
Planned agents:
- DocumentAnalysisAgent
- EvidenceExtractionAgent
- LegalResearchAgent
- ArgumentConstructionAgent
- CourtroomSimulationAgent
- AccountabilityAgent
"""
from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """Abstract base for all Court Vision AI agents."""

    @abstractmethod
    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute the agent with the given context."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable agent name."""
        ...
