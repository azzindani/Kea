"""
Knowledge Store.

Thin wrapper around PostgresKnowledgeRegistry for the RAG service,
providing knowledge retrieval capabilities alongside the existing
FactStore and ArtifactStore.
"""

from __future__ import annotations

from typing import Any

from shared.knowledge.registry import PostgresKnowledgeRegistry
from shared.logging import get_logger

logger = get_logger(__name__)


class KnowledgeStore:
    """
    Store and retrieve knowledge items (skills, rules, personas).

    Wraps PostgresKnowledgeRegistry for use within the RAG service.
    """

    def __init__(self) -> None:
        self._registry = PostgresKnowledgeRegistry()

    async def search(
        self,
        query: str,
        limit: int = 5,
        domain: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Semantic search for knowledge items."""
        return await self._registry.search(
            query=query,
            limit=limit,
            domain=domain,
            category=category,
            tags=tags,
        )

    async def get_by_id(self, knowledge_id: str) -> dict[str, Any] | None:
        """Get a knowledge item by ID."""
        return await self._registry.get_by_id(knowledge_id)

    async def sync(self, items: list[dict[str, Any]]) -> int:
        """Sync knowledge items to the registry."""
        return await self._registry.sync_knowledge(items)

    async def count(self) -> int:
        """Get total number of indexed knowledge items."""
        return await self._registry.count()


def create_knowledge_store() -> KnowledgeStore:
    """Create a KnowledgeStore instance."""
    return KnowledgeStore()
