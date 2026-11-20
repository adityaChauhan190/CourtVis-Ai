"""
Court Vision AI — Graph Package (Phase 5+)

Future: Neo4j case knowledge graph + Phase 6 GNN inference.
Components:
- GraphService: Neo4j driver abstraction
- EntityNode: legal entity representation
- EvidenceEdge: relationship between evidence
- CaseGraphBuilder: constructs knowledge graph from NLP output
- GNNService (Phase 6): PyTorch Geometric inference
"""
from abc import ABC, abstractmethod
from typing import Any


class GraphService(ABC):
    """Interface for knowledge graph operations."""

    @abstractmethod
    async def add_entity(self, case_id: str, entity: dict[str, Any]) -> str:
        ...

    @abstractmethod
    async def add_relationship(
        self, source_id: str, target_id: str, relationship_type: str, properties: dict
    ) -> None:
        ...

    @abstractmethod
    async def query(self, cypher: str, params: dict | None = None) -> list[dict]:
        ...
