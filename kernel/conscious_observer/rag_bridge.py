"""
Tier 7 Conscious Observer — RAG Bridge.

Bridges the Conscious Observer to RAG Knowledge and Tool retrieval systems,
enabling the Human Kernel to be self-sufficient in dynamic knowledge and
tool selection.

Architecture:
- Knowledge retrieval via KnowledgeRetriever (HTTP → RAG Service)
- Tool retrieval via PostgresToolRegistry (existing, tested tool search)
- Validation via kernel/validation/engine.py (existing 5-gate cascade)

Design Principles:
- Knowledge: Retrieved ONCE at Gate-In → becomes agent identity/memory
- Tools: Retrieved DYNAMICALLY per task/subtask at Execute phase
- Reuses existing kernel modules — no redundant standalone wrappers
- Graceful degradation: RAG failures return empty results, never crash
- Parallel retrieval: asyncio.gather for concurrent RAG calls
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from shared.config import get_settings
from shared.knowledge.retriever import KnowledgeRetriever, get_knowledge_retriever
from shared.logging.main import get_logger
from services.mcp_host.core.tool_registry import get_tool_registry

from kernel.conscious_observer.types import (
    RAGEnrichmentResult,
    RAGKnowledgeResult,
    RAGToolResult,
)
from kernel.lifecycle_controller.types import CognitiveProfile
from kernel.self_model.types import SignalTags

log = get_logger(__name__)


class RAGBridge:
    """Bridges Conscious Observer to RAG subsystems.

    Reuses existing kernel components:
    - KnowledgeRetriever (HTTP → RAG Service) for knowledge
    - PostgresToolRegistry (pgvector semantic search) for tools
    - kernel/validation/engine.py for schema validation

    All methods are designed for graceful degradation — service outages
    produce empty results rather than exceptions.
    """

    def __init__(self) -> None:
        self._knowledge: KnowledgeRetriever = get_knowledge_retriever()

    # ========================================================================
    # Tier A: Knowledge Retrieval (ONE-TIME at Gate-In)
    # ========================================================================

    async def retrieve_knowledge(
        self,
        objective: str,
        role: str,
        domain: str | None = None,
    ) -> RAGKnowledgeResult:
        """Retrieve persona, rules, skills, and procedures in parallel.

        Called once during Gate-In to form the agent's cognitive identity.
        Uses the objective and role to construct semantic search queries.

        Args:
            objective: Agent's prime directive (from SpawnRequest).
            role: Agent's assigned role (from SpawnRequest).
            domain: Optional knowledge domain hint.

        Returns:
            RAGKnowledgeResult with separated context per category.
        """
        settings = get_settings()
        ks = settings.kernel
        start = time.perf_counter()

        # Construct the semantic query from objective + role
        search_query = f"{role}: {objective}"

        try:
            # Parallel retrieval of all 4 knowledge categories
            persona_task = self._knowledge.retrieve_context(
                query=search_query,
                limit=ks.rag_knowledge_persona_limit,
                domain=domain,
                category="persona",
            )
            rules_task = self._knowledge.retrieve_rules(
                query=search_query,
                limit=ks.rag_knowledge_rule_limit,
                domain=domain,
            )
            skills_task = self._knowledge.retrieve_skills(
                query=search_query,
                limit=ks.rag_knowledge_skill_limit,
                domain=domain,
            )
            procedures_task = self._knowledge.retrieve_procedures(
                query=search_query,
                limit=ks.rag_knowledge_procedure_limit,
                domain=domain,
            )

            results = await asyncio.gather(
                persona_task,
                rules_task,
                skills_task,
                procedures_task,
                return_exceptions=True,
            )

            # Extract results (graceful — exceptions become empty strings)
            persona_ctx = results[0] if isinstance(results[0], str) else ""
            rules_ctx = results[1] if isinstance(results[1], str) else ""
            skills_ctx = results[2] if isinstance(results[2], str) else ""
            procedures_ctx = results[3] if isinstance(results[3], str) else ""

            # Also retrieve raw items for name extraction
            raw_items = await self._retrieve_raw_names(
                search_query, domain
            )

            # Combine into formatted context
            parts = [p for p in [persona_ctx, rules_ctx, skills_ctx, procedures_ctx] if p]
            formatted = "\n\n".join(parts)

            elapsed_ms = (time.perf_counter() - start) * 1000

            result = RAGKnowledgeResult(
                formatted_context=formatted,
                persona_context=persona_ctx,
                rules_context=rules_ctx,
                skills_context=skills_ctx,
                procedures_context=procedures_ctx,
                skills_found=raw_items.get("skills", []),
                rules_found=raw_items.get("rules", []),
                procedures_found=raw_items.get("procedures", []),
                knowledge_domains=raw_items.get("domains", []),
                retrieval_ms=elapsed_ms,
            )

            log.info(
                "Knowledge retrieved for Gate-In",
                objective=objective[:80],
                role=role,
                skills=len(result.skills_found),
                rules=len(result.rules_found),
                procedures=len(result.procedures_found),
                domains=result.knowledge_domains,
                elapsed_ms=round(elapsed_ms, 1),
            )

            return result

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            log.warning(
                "Knowledge retrieval failed — proceeding without knowledge",
                error=str(exc),
                elapsed_ms=round(elapsed_ms, 1),
            )
            return RAGKnowledgeResult(retrieval_ms=elapsed_ms)

    async def _retrieve_raw_names(
        self,
        query: str,
        domain: str | None,
    ) -> dict[str, list[str]]:
        """Extract skill/rule/procedure names and domains from raw search.

        Uses search_raw to get structured results with metadata,
        then extracts names for CognitiveProfile enrichment.
        """
        result: dict[str, list[str]] = {
            "skills": [],
            "rules": [],
            "procedures": [],
            "domains": [],
        }

        try:
            settings = get_settings()
            total_limit = (
                settings.kernel.rag_knowledge_skill_limit
                + settings.kernel.rag_knowledge_rule_limit
                + settings.kernel.rag_knowledge_procedure_limit
            )

            raw_items = await self._knowledge.search_raw(
                query=query,
                limit=total_limit,
                domain=domain,
            )

            seen_domains: set[str] = set()

            for item in raw_items:
                name = item.get("name", "")
                category = item.get("category", "")
                item_domain = item.get("domain", "")

                if not name:
                    continue

                if category == "skill":
                    result["skills"].append(name)
                elif category == "rule":
                    result["rules"].append(name)
                elif category == "procedure":
                    result["procedures"].append(name)

                if item_domain and item_domain not in seen_domains:
                    seen_domains.add(item_domain)
                    result["domains"].append(item_domain)

        except Exception as exc:
            log.debug(
                "Raw name extraction failed — using empty names",
                error=str(exc),
            )

        return result

    # ========================================================================
    # Tier B: Tool Retrieval (DYNAMIC per task/subtask)
    # Uses PostgresToolRegistry directly — same path as rag_retrieval.py tests
    # ========================================================================

    async def retrieve_tools(
        self,
        objective: str,
        signal_tags: SignalTags | None = None,
        entities: list[Any] | None = None,
        exclude_tools: list[str] | None = None,
    ) -> RAGToolResult:
        """Semantic tool retrieval using existing PostgresToolRegistry.

        Uses the same search_tools() that rag_retrieval.py tests against.

        Args:
            objective: Current objective or subtask description.
            signal_tags: T1 perception tags with domain, intent, keywords.
            entities: Extracted entities for query enrichment.
            exclude_tools: Blacklisted tool names to filter out.

        Returns:
            RAGToolResult with tool schemas and names.
        """
        settings = get_settings()
        ks = settings.kernel
        start = time.perf_counter()

        # Build semantic query from available signal context
        query = self._build_tool_query(objective, signal_tags, entities)

        try:
            registry = await get_tool_registry()
            tools = await registry.search_tools(
                query=query,
                limit=ks.rag_tool_search_limit,
                min_similarity=ks.rag_tool_min_similarity,
            )

            # Filter out blacklisted tools
            if exclude_tools:
                excluded_set = set(exclude_tools)
                tools = [
                    t for t in tools
                    if t.get("name", "") not in excluded_set
                ]

            elapsed_ms = (time.perf_counter() - start) * 1000
            tool_names = [t.get("name", "") for t in tools if t.get("name")]

            log.info(
                "Tools retrieved for Execute",
                query=query[:80],
                total=len(tools),
                excluded=len(exclude_tools or []),
                elapsed_ms=round(elapsed_ms, 1),
            )

            return RAGToolResult(
                tool_schemas=tools,
                tool_names=tool_names,
                retrieval_ms=elapsed_ms,
            )

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            log.warning(
                "Tool retrieval failed — proceeding without tools",
                error=str(exc),
                elapsed_ms=round(elapsed_ms, 1),
            )
            return RAGToolResult(retrieval_ms=elapsed_ms)

    @staticmethod
    def _build_tool_query(
        objective: str,
        signal_tags: SignalTags | None,
        entities: list[Any] | None,
    ) -> str:
        """Construct semantic query for tool search.

        Combines objective with signal context (domain, intent, keywords,
        entities) for optimal semantic matching.
        """
        parts: list[str] = [objective]

        if signal_tags:
            if signal_tags.domain and signal_tags.domain != "general":
                parts.append(f"domain:{signal_tags.domain}")
            if signal_tags.intent and signal_tags.intent != "unknown":
                parts.append(f"intent:{signal_tags.intent}")
            if signal_tags.content_keywords:
                keywords = " ".join(list(signal_tags.content_keywords)[:5])
                parts.append(keywords)

        if entities:
            # Extract entity text/labels for query enrichment
            entity_texts = []
            for ent in entities[:3]:
                if hasattr(ent, "text"):
                    entity_texts.append(ent.text)
                elif hasattr(ent, "value"):
                    entity_texts.append(str(ent.value))
            if entity_texts:
                parts.append(" ".join(entity_texts))

        return " ".join(parts)

    # ========================================================================
    # Profile Enrichment
    # ========================================================================

    @staticmethod
    def enrich_cognitive_profile(
        profile: CognitiveProfile,
        knowledge: RAGKnowledgeResult,
    ) -> CognitiveProfile:
        """Enrich a CognitiveProfile with RAG-discovered knowledge.

        Merges retrieved skill names into profile.skills and discovered
        knowledge domains into profile.knowledge_domains.

        Does NOT mutate the original — returns a new copy.

        Args:
            profile: Base cognitive profile from lifecycle genesis.
            knowledge: Knowledge results from RAG retrieval.

        Returns:
            New CognitiveProfile with enriched skills and domains.
        """
        # Merge skills (deduplicated)
        existing_skills = set(profile.skills)
        new_skills = [s for s in knowledge.skills_found if s not in existing_skills]
        merged_skills = list(profile.skills) + new_skills

        # Merge knowledge domains (deduplicated)
        existing_domains = set(profile.knowledge_domains)
        new_domains = [d for d in knowledge.knowledge_domains if d not in existing_domains]
        merged_domains = list(profile.knowledge_domains) + new_domains

        enriched = profile.model_copy(
            update={
                "skills": merged_skills,
                "knowledge_domains": merged_domains,
            }
        )

        if new_skills or new_domains:
            log.info(
                "CognitiveProfile enriched with RAG knowledge",
                new_skills=new_skills,
                new_domains=new_domains,
                total_skills=len(merged_skills),
                total_domains=len(merged_domains),
            )

        return enriched
