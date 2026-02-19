"""
Knowledge-Enhanced Inference Engine.

Wraps every LLM call with contextual knowledge retrieval and structured output
parsing. This is the central inference layer that ensures every LLM call in the
kernel receives role-specific domain knowledge.

Instead of:
    provider.complete(messages, config)

Use:
    engine = get_inference_engine()
    result = await engine.complete(messages, config, context)

Features:
- Role-specific knowledge retrieval (skills, rules, procedures)
- Structured output parsing via Pydantic schemas
- Token budget tracking per inference call
- Prompt assembly: base_prompt + identity + knowledge + constraints
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Type, TypeVar

from pydantic import BaseModel, Field

from shared.utils.parsing import parse_llm_json

from shared.knowledge.retriever import KnowledgeRetriever, get_knowledge_retriever
from shared.llm import LLMConfig, OpenRouterProvider
from shared.llm.provider import LLMMessage, LLMResponse, LLMRole
from shared.logging import get_logger
from shared.prompts import get_kernel_config
from kernel.awareness.context_fusion import AwarenessEnvelope

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

# Module-level singleton
_engine: KnowledgeEnhancedInference | None = None


# ============================================================================
# Inference Context   What Each LLM Call Knows
# ============================================================================


@dataclass
class AgentIdentity:
    """
    Identity profile for a kernel cell.

    Determines WHO is calling the LLM, which drives:
    - What knowledge gets retrieved
    - What tool access is allowed
    - What quality bar is applied
    """

    role: str = "researcher"                    # e.g., "financial_analyst", "critic"
    level: str = "staff"                        # staff | manager | director | vp | ceo
    domain: str = "general"                     # finance, technology, etc.
    persona: str = ""                           # Human-readable persona description
    skills: list[str] = field(default_factory=list)  # Skill IDs loaded from knowledge
    tool_access: list[str] = field(default_factory=list)  # Tool patterns allowed

    @property
    def identity_prompt(self) -> str:
        """Generate the identity section of the system prompt."""
        parts = [
            f"You are a {self.level}-level {self.role} specializing in {self.domain}.",
        ]
        if self.persona:
            parts.append(self.persona)
        return " ".join(parts)


@dataclass
class InferenceContext:
    """
    Context provided to every LLM inference call.

    Controls what knowledge is retrieved, how the prompt is assembled,
    and what output schema is expected.
    """

    # WHO is calling
    identity: AgentIdentity = field(default_factory=AgentIdentity)

    # WHAT knowledge to retrieve
    skill_query: str = ""           # Query for skill retrieval (may differ from user query)
    skill_limit: int = 3            # How many skills to inject
    rule_limit: int = 2             # How many rules to inject
    procedure_limit: int = 2        # How many procedures to inject
    domain_filter: str | None = None  # Filter knowledge by domain

    # HOW to structure output
    output_schema: type[BaseModel] | None = None  # Pydantic model for structured output

    # CONSTRAINTS
    quality_bar: str = "professional"  # draft | professional | executive

    # TRACKING
    task_description: str = ""       # What this inference is for
    parent_cell_id: str = ""         # Which kernel cell initiated this
    
    # NEW: Situational Awareness (Phase 1)
    awareness: AwarenessEnvelope | None = None

    # NEW: Episodic Memory (Phase 3)
    past_episodes: list[dict[str, Any]] = field(default_factory=list)

    @property
    def retrieval_query(self) -> str:
        """The query to use for knowledge retrieval."""
        return self.skill_query or self.task_description


# ============================================================================
# Retrieved Knowledge Bundle
# ============================================================================


@dataclass
class KnowledgeBundle:
    """Knowledge retrieved for a specific inference call."""

    skills: str = ""          # Formatted skill context
    rules: str = ""           # Formatted rule context
    procedures: str = ""      # Formatted procedure context
    raw_items: int = 0        # Total items retrieved

    @property
    def has_content(self) -> bool:
        """Check if any knowledge was retrieved."""
        return bool(self.skills or self.rules or self.procedures)

    def to_prompt_section(self) -> str:
        """Format all knowledge into a prompt-injectable section."""
        if not self.has_content:
            return ""

        sections = []

        if self.skills:
            sections.append(self.skills)

        if self.rules:
            sections.append(f"\n## RULES & CONSTRAINTS\n{self.rules}")

        if self.procedures:
            sections.append(f"\n## STANDARD OPERATING PROCEDURES\n{self.procedures}")

        return "\n\n".join(sections)


# ============================================================================
# Knowledge-Enhanced Inference Engine
# ============================================================================


class KnowledgeEnhancedInference:
    """
    Wraps every LLM call with contextual knowledge retrieval.

    This is the central inference layer for the kernel. It:
    1. Retrieves role-specific knowledge (skills, rules, procedures)
    2. Assembles an enhanced system prompt (identity + knowledge + task)
    3. Calls the LLM with structured output instructions
    4. Parses and validates the response into a Pydantic model

    Usage:
        engine = get_inference_engine()

        # Unstructured call with knowledge injection
        response = await engine.complete(messages, config, context)

        # Structured call with Pydantic output validation
        result = await engine.structured_complete(
            messages, config, context, output_schema=PlannerOutput,
        )
    """

    def __init__(
        self,
        retriever: KnowledgeRetriever | None = None,
        provider: OpenRouterProvider | None = None,
    ) -> None:
        self.retriever = retriever or get_knowledge_retriever()
        self.provider = provider or OpenRouterProvider()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    async def complete(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
        context: InferenceContext | None = None,
    ) -> LLMResponse:
        """
        Complete with knowledge injection (unstructured output).

        If context is provided, retrieves relevant knowledge and enhances
        the system prompt before calling the LLM.
        """
        if context:
            messages = await self._enhance_messages(messages, context)

        response = await self.provider.complete(messages, config)

        logger.info(
            f"Inference complete: "
            f"role={getattr(context, 'identity', AgentIdentity()).role} "
            f"tokens={response.usage.total_tokens}"
        )

        return response

    async def structured_complete(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
        context: InferenceContext | None = None,
        output_schema: type[T] | None = None,
    ) -> T | LLMResponse:
        """
        Complete with knowledge injection + structured Pydantic output.

        If output_schema is provided (either here or in context), appends
        JSON schema instructions to the system prompt and parses the response
        into the Pydantic model.

        Returns:
            Validated Pydantic model instance, or LLMResponse if no schema.
        """
        schema = output_schema or (context.output_schema if context else None)

        if context:
            messages = await self._enhance_messages(messages, context, schema)
        elif schema:
            messages = self._append_schema_instruction(messages, schema)

        response = await self.provider.complete(messages, config)

        if schema:
            try:
                parsed = self._parse_structured(response.content, schema)
                logger.info(
                    f"Structured inference: schema={schema.__name__} "
                    f"tokens={response.usage.total_tokens}"
                )
                return parsed
            except Exception as e:
                logger.warning(
                    f"Structured parsing failed for {schema.__name__}: {e}. "
                    f"Returning raw response."
                )
                return response

        return response

    async def retrieve_knowledge(
        self,
        context: InferenceContext,
    ) -> KnowledgeBundle:
        """
        Retrieve knowledge bundle for a given inference context.

        Can be called independently to pre-fetch knowledge for
        prompt assembly outside this engine.
        """
        return await self._retrieve_knowledge(context)

    # ------------------------------------------------------------------ #
    # Internal: Knowledge Retrieval
    # ------------------------------------------------------------------ #

    async def _retrieve_knowledge(
        self,
        context: InferenceContext,
    ) -> KnowledgeBundle:
        """Retrieve role-specific knowledge from the knowledge registry."""
        query = context.retrieval_query
        if not query:
            return KnowledgeBundle()

        domain = context.domain_filter or context.identity.domain

        try:
            import asyncio

            # Parallel retrieval of skills, rules, and procedures
            skills_coro = self.retriever.retrieve_skills(
                query=query,
                limit=context.skill_limit,
                domain=domain if domain != "general" else None,
            )
            rules_coro = self.retriever.retrieve_rules(
                query=query,
                limit=context.rule_limit,
                domain=domain if domain != "general" else None,
            )
            procedures_coro = self.retriever.retrieve_procedures(
                query=query,
                limit=context.procedure_limit,
                domain=domain if domain != "general" else None,
            )

            skills, rules, procedures = await asyncio.gather(
                skills_coro, rules_coro, procedures_coro,
                return_exceptions=True,
            )

            bundle = KnowledgeBundle(
                skills=skills if isinstance(skills, str) else "",
                rules=rules if isinstance(rules, str) else "",
                procedures=procedures if isinstance(procedures, str) else "",
            )

            # Count items
            raw_count = 0
            for section in [bundle.skills, bundle.rules, bundle.procedures]:
                if section:
                    # Count "---" separators as proxy for items
                    raw_count += section.count("--- ")

            bundle.raw_items = raw_count

            if bundle.has_content:
                logger.info(
                    f"Knowledge retrieved: {raw_count} items for "
                    f"role={context.identity.role} domain={domain}"
                )

            return bundle

        except Exception as e:
            logger.warning(f"Knowledge retrieval failed: {e}")
            return KnowledgeBundle()

    # ------------------------------------------------------------------ #
    # Internal: Prompt Assembly
    # ------------------------------------------------------------------ #

    async def _enhance_messages(
        self,
        messages: list[LLMMessage],
        context: InferenceContext,
        schema: type[BaseModel] | None = None,
    ) -> list[LLMMessage]:
        """Enhance messages with identity + knowledge + schema instructions."""
        # Make a copy to avoid mutating the original
        messages = [LLMMessage(role=m.role, content=m.content) for m in messages]

        # Retrieve knowledge
        knowledge = await self._retrieve_knowledge(context)

        # Find or create system message
        system_idx = None
        for i, msg in enumerate(messages):
            if msg.role == LLMRole.SYSTEM:
                system_idx = i
                break

        if system_idx is None:
            messages.insert(0, LLMMessage(role=LLMRole.SYSTEM, content=""))
            system_idx = 0

        # Assemble enhanced system prompt
        parts: list[str] = []

        # 0. Situational Awareness (Crucial Context - First thing the model sees)
        if context.awareness:
            parts.append(context.awareness.to_system_prompt())

        # 1. Agent identity
        parts.append(context.identity.identity_prompt)

        # 2. Original system prompt
        original = messages[system_idx].content
        if original:
            parts.append(original)

        # 3. Knowledge injection
        knowledge_section = knowledge.to_prompt_section()
        if knowledge_section:
            parts.append(f"\n{knowledge_section}")
        
        # 3.5 Episodic Memory Injection
        if context.past_episodes:
            ep_parts = ["## RELEVANT PAST EXPERIENCES (LEARN FROM THESE)"]
            for i, ep in enumerate(context.past_episodes):
                ep_parts.append(
                    f"\n[Episode {i+1}] Query: {ep.get('query', '')}\n"
                    f"Outcome: {ep.get('outcome', '')[:300]}..."
                )
            parts.append("\n".join(ep_parts))

        # 4. Quality bar instruction
         
        quality_instruction = self._quality_instruction(context.quality_bar)
        if quality_instruction:
            parts.append(quality_instruction)

        # 5. Schema instruction
        effective_schema = schema or context.output_schema
        if effective_schema:
            parts.append(self._schema_instruction(effective_schema))

        messages[system_idx] = LLMMessage(
            role=LLMRole.SYSTEM,
            content="\n\n".join(parts),
        )

        return messages

    def _append_schema_instruction(
        self,
        messages: list[LLMMessage],
        schema: type[BaseModel],
    ) -> list[LLMMessage]:
        """Append schema instruction to the system message (no knowledge)."""
        messages = [LLMMessage(role=m.role, content=m.content) for m in messages]

        for i, msg in enumerate(messages):
            if msg.role == LLMRole.SYSTEM:
                messages[i] = LLMMessage(
                    role=LLMRole.SYSTEM,
                    content=msg.content + "\n\n" + self._schema_instruction(schema),
                )
                return messages

        # No system message found, prepend one
        messages.insert(0, LLMMessage(
            role=LLMRole.SYSTEM,
            content=self._schema_instruction(schema),
        ))
        return messages

    def _schema_instruction(self, schema: type[BaseModel]) -> str:
        """Generate the JSON schema instruction for structured output."""
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        return (
            "## OUTPUT FORMAT (MANDATORY)\n"
            "You MUST respond with valid JSON matching this exact schema. "
            "Do NOT include markdown code fences   output raw JSON only.\n\n"
            f"```json\n{schema_json}\n```"
        )

    def _quality_instruction(self, quality_bar: str) -> str:
        """Generate quality bar instruction from config."""
        # Load from kernel.yaml   editable without touching Python
        config_instructions = get_kernel_config(
            "kernel_cell.quality_instructions",
        )
        if isinstance(config_instructions, dict) and quality_bar in config_instructions:
            return f"## QUALITY: {quality_bar.upper()}\n{config_instructions[quality_bar]}"

        # Fallback defaults (in case config is missing)
        _defaults = {
            "draft": (
                "## QUALITY: DRAFT\n"
                "Prioritize speed and coverage over polish. "
                "Incomplete data is acceptable   flag gaps clearly."
            ),
            "professional": (
                "## QUALITY: PROFESSIONAL\n"
                "Deliver thorough, well-structured, verified output. "
                "Cross-reference data points. Cite sources."
            ),
            "executive": (
                "## QUALITY: EXECUTIVE\n"
                "Deliver boardroom-ready output: precise language, "
                "no filler, actionable insights, quantified claims, "
                "risk-aware recommendations with confidence levels."
            ),
        }
        return _defaults.get(quality_bar, "")

    # ------------------------------------------------------------------ #
    # Internal: Structured Parse
    # ------------------------------------------------------------------ #

    def _parse_structured(self, content: str, schema: Type[T]) -> T:
        """
        Parse LLM response content into a Pydantic model.

        Handles common LLM formatting quirks (markdown fences, whitespace).
        """
        return parse_llm_json(content, schema)


# ============================================================================
# Singleton Access
# ============================================================================


def get_inference_engine(
    retriever: KnowledgeRetriever | None = None,
    provider: OpenRouterProvider | None = None,
) -> KnowledgeEnhancedInference:
    """Get or create the global inference engine singleton."""
    global _engine
    if _engine is None:
        _engine = KnowledgeEnhancedInference(
            retriever=retriever,
            provider=provider,
        )
    return _engine
