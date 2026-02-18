"""
Knowledge Retriever.

High-level API for retrieving domain-specific knowledge context
and formatting it for injection into LLM system prompts.

Routes all knowledge searches through the RAG Service REST API (port 8003)
to maintain microservice isolation — no direct database access.

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
import time
from typing import Any

import httpx

from shared.logging import get_logger
from shared.service_registry import ServiceName, ServiceRegistry

logger = get_logger(__name__)

# Module-level singleton
_retriever: KnowledgeRetriever | None = None


class KnowledgeRetriever:
    """
    Retrieves and formats knowledge context for LLM prompt injection.

    Calls the RAG Service's /knowledge/search endpoint — no direct DB access.
    """

    def __init__(self) -> None:
        # Simple in-memory cache: (key) -> (timestamp, result)
        # Key: (query, domain, category, tags_tuple, limit)
        self._cache: dict[tuple, tuple[float, str]] = {}
        self._cache_ttl = 60.0  # 60s TTL

    def _rag_url(self) -> str:
        return ServiceRegistry.get_url(ServiceName.RAG_SERVICE)

    async def retrieve_context(
        self,
        query: str,
        limit: int = 3,
        domain: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        min_similarity: float = 0.3,
        enable_reranking: bool = False,
    ) -> str:
        """
        Retrieve formatted knowledge context for prompt injection.

        Features:
        - In-memory caching (60s TTL)
        - Structured logging of selected items
        - Routes through RAG Service API — no direct Postgres access
        """
        # Check cache first
        tags_tuple = tuple(sorted(tags)) if tags else None
        cache_key = (query, domain, category, tags_tuple, limit)

        now = time.time()
        if cache_key in self._cache:
            timestamp, cached_result = self._cache[cache_key]
            if now - timestamp < self._cache_ttl:
                logger.debug(f"Knowledge Cache Hit: {category}/{domain} for '{query[:30]}...'")
                return cached_result

        payload: dict[str, Any] = {"query": query, "limit": limit}
        if domain:
            payload["domain"] = domain
        if category:
            payload["category"] = category
        if tags:
            payload["tags"] = tags
        
        payload["enable_reranking"] = enable_reranking

        label = f"category={category or 'all'} domain={domain or 'any'}"
        logger.debug(f"KnowledgeRetriever: querying RAG Service [{label}] q='{query[:60]}'")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self._rag_url()}/knowledge/search",
                    json=payload,
                )
                if resp.status_code != 200:
                    logger.warning(
                        f"KnowledgeRetriever: RAG Service returned {resp.status_code} [{label}]"
                    )
                    return ""
                results: list[dict[str, Any]] = resp.json()

            if not results:
                logger.debug(f"KnowledgeRetriever: no items found [{label}]")
                return ""

            log_items = [
                f"{r.get('knowledge_id', '?')} ({r.get('similarity', 0.0):.2f})" for r in results
            ]
            logger.info(f"KnowledgeRetriever: {len(results)} items [{label}] -> {log_items}")

            relevant = [r for r in results if r.get("similarity", 0) >= min_similarity]
            
            # Fallback logic: if no items meet strict threshold, return what we found
            # The user explicitly requested "real output... make it fall back"
            if not relevant and results:
                logger.warning(
                    f"KnowledgeRetriever: Strict threshold {min_similarity} yielded 0 items. "
                    f"Falling back to {len(results)} items with low similarity [{label}]"
                )
                relevant = results

            # Final check (should only be empty if results was empty)
            if not relevant:
                logger.debug(
                    f"KnowledgeRetriever: all {len(results)} items below "
                    f"similarity threshold {min_similarity} [{label}]"
                )
                return ""

            formatted = self._format_context(relevant)
            logger.info(
                f"KnowledgeRetriever: injecting {len(relevant)} knowledge items "
                f"({len(formatted)} chars) into system prompt [{label}]"
            )
            self._cache[cache_key] = (now, formatted)
            return formatted

        except httpx.TimeoutException:
            logger.warning("KnowledgeRetriever: RAG Service request timed out")
            return ""
        except Exception as e:
            logger.warning(f"KnowledgeRetriever: Search failed: {type(e).__name__}: {e}")
            return ""

    async def search_raw(
        self,
        query: str,
        limit: int = 5,
        domain: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve raw knowledge items without formatting.
        
        Useful for programmatic usage (e.g., loading examples for classifiers).
        """
        payload: dict[str, Any] = {"query": query, "limit": limit}
        if domain:
            payload["domain"] = domain
        if category:
            payload["category"] = category
        if tags:
            payload["tags"] = tags
            
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self._rag_url()}/knowledge/search",
                    json=payload,
                )
                if resp.status_code == 200:
                    return resp.json()
                return []
        except Exception as e:
            logger.warning(f"KnowledgeRetriever: Raw search failed: {type(e).__name__}: {e}")
            return []

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

    async def retrieve_procedures(
        self,
        query: str,
        limit: int = 3,
        domain: str | None = None,
    ) -> str:
        """Retrieve procedure-type knowledge (Standard Operating Procedures)."""
        return await self.retrieve_context(
            query=query,
            limit=limit,
            domain=domain,
            category="procedure",
        )

    async def retrieve_all(
        self,
        query: str,
        skill_limit: int = 3,
        rule_limit: int = 2,
        procedure_limit: int = 2,
        domain: str | None = None,
    ) -> str:
        """
        Retrieve combined context (Skills + Rules + Procedures).

        Returns combined formatted context with skills, rules, and procedures sections.
        """
        skills, rules, procedures = await asyncio.gather(
            self.retrieve_skills(query, limit=skill_limit, domain=domain),
            self.retrieve_rules(query, limit=rule_limit, domain=domain),
            self.retrieve_procedures(query, limit=procedure_limit, domain=domain),
            return_exceptions=True,
        )

        parts = []
        if isinstance(skills, str) and skills:
            parts.append(skills)
        if isinstance(rules, str) and rules:
            parts.append(rules)
        if isinstance(procedures, str) and procedures:
            parts.append(procedures)

        return "\n\n".join(parts)

    async def is_available(self) -> bool:
        """Check if the RAG Service knowledge endpoint is reachable."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self._rag_url()}/health")
                return resp.status_code == 200
        except Exception:
            return False

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
