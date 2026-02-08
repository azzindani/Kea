"""
Knowledge Retriever.

High-level API for retrieving domain-specific knowledge context
and formatting it for injection into LLM system prompts.

Usage:
    retriever = get_knowledge_retriever()
    context = await retriever.retrieve_context(
        query="Analyze Tesla's balance sheet",
        limit=3,
    )
    # context is a formatted string ready for prompt injection
"""

from __future__ import annotations

import asyncio
from typing import Any

from shared.logging import get_logger

logger = get_logger(__name__)

# Module-level singleton
_retriever: KnowledgeRetriever | None = None


class KnowledgeRetriever:
    """
    Retrieves and formats knowledge context for LLM prompt injection.

    Wraps PostgresKnowledgeRegistry with caching and formatting logic.
    """

    def __init__(self) -> None:
        self._registry: Any = None
        self._available = False
        self._init_attempted = False

    async def _ensure_registry(self) -> bool:
        """Lazily initialize the registry connection."""
        if self._init_attempted:
            return self._available

        self._init_attempted = True
        try:
            from shared.knowledge.registry import PostgresKnowledgeRegistry

            self._registry = PostgresKnowledgeRegistry()
            # Test the connection by getting the pool
            await self._registry._get_pool()
            self._available = True
            logger.info("KnowledgeRetriever: Connected to knowledge registry")
        except Exception as e:
            logger.warning(f"KnowledgeRetriever: Unavailable ({e}). Proceeding without.")
            self._available = False

        return self._available

    async def retrieve_context(
        self,
        query: str,
        limit: int = 3,
        domain: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        min_similarity: float = 0.3,
    ) -> str:
        """
        Retrieve formatted knowledge context for prompt injection.

        Args:
            query: User query or task description
            limit: Max number of knowledge items to retrieve
            domain: Optional domain filter (e.g., "finance")
            category: Optional category filter ("skill", "rule", "persona")
            tags: Optional tag filter
            min_similarity: Minimum similarity threshold

        Returns:
            Formatted string ready for system prompt injection,
            or empty string if no relevant knowledge found.
        """
        if not await self._ensure_registry():
            return ""

        try:
            results = await asyncio.wait_for(
                self._registry.search(
                    query=query,
                    limit=limit,
                    domain=domain,
                    category=category,
                    tags=tags,
                ),
                timeout=5.0,
            )

            if not results:
                return ""

            # Filter by similarity threshold
            relevant = [r for r in results if r.get("similarity", 0) >= min_similarity]

            if not relevant:
                return ""

            return self._format_context(relevant)

        except TimeoutError:
            logger.warning("KnowledgeRetriever: Search timed out")
            return ""
        except Exception as e:
            logger.warning(f"KnowledgeRetriever: Search failed ({e})")
            return ""

    async def retrieve_skills(
        self,
        query: str,
        limit: int = 3,
        domain: str | None = None,
    ) -> str:
        """Retrieve skill-type knowledge (reasoning frameworks, mental models)."""
        return await self.retrieve_context(
            query=query,
            limit=limit,
            domain=domain,
            category="skill",
        )

    async def retrieve_rules(
        self,
        query: str,
        limit: int = 2,
        domain: str | None = None,
    ) -> str:
        """Retrieve rule-type knowledge (governance, safety constraints)."""
        return await self.retrieve_context(
            query=query,
            limit=limit,
            domain=domain,
            category="rule",
        )

    async def retrieve_all(
        self,
        query: str,
        skill_limit: int = 3,
        rule_limit: int = 2,
        domain: str | None = None,
    ) -> str:
        """
        Retrieve both skills and rules for comprehensive context.

        Returns combined formatted context with skills and rules sections.
        """
        skills, rules = await asyncio.gather(
            self.retrieve_skills(query, limit=skill_limit, domain=domain),
            self.retrieve_rules(query, limit=rule_limit, domain=domain),
            return_exceptions=True,
        )

        parts = []
        if isinstance(skills, str) and skills:
            parts.append(skills)
        if isinstance(rules, str) and rules:
            parts.append(rules)

        return "\n\n".join(parts)

    async def is_available(self) -> bool:
        """Check if the knowledge registry is available."""
        return await self._ensure_registry()

    def _format_context(self, items: list[dict[str, Any]]) -> str:
        """Format retrieved knowledge items into a prompt-ready string."""
        if not items:
            return ""

        sections = []
        for item in items:
            category = item.get("category", "skill").upper()
            name = item.get("name", "Unknown")
            domain = item.get("domain", "general")
            similarity = item.get("similarity", 0)
            content = item.get("content", "")

            section = (
                f"--- {category}: {name} (domain: {domain}, "
                f"relevance: {similarity:.0%}) ---\n"
                f"{content}"
            )
            sections.append(section)

        header = f"DOMAIN EXPERTISE ({len(items)} relevant knowledge items):"
        return header + "\n\n" + "\n\n".join(sections)


def get_knowledge_retriever() -> KnowledgeRetriever:
    """Get or create global KnowledgeRetriever singleton."""
    global _retriever
    if _retriever is None:
        _retriever = KnowledgeRetriever()
    return _retriever
