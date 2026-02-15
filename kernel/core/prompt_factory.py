"""
System Prompt Factory.

Generate specialized system prompts for different domains and tasks.
Same LLM model + different prompts = different specializations.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from kernel.core.organization import Domain
from shared.logging import get_logger

logger = get_logger(__name__)


class TaskType(str, Enum):
    """Task types requiring different approaches."""

    RESEARCH = "research"  # Deep investigation
    ANALYSIS = "analysis"  # Data analysis
    SUMMARIZE = "summarize"  # Condensing information
    COMPARE = "compare"  # Comparison of entities
    EXTRACT = "extract"  # Extract specific data
    VALIDATE = "validate"  # Fact-checking
    FORECAST = "forecast"  # Predictions
    EXPLAIN = "explain"  # Explanations


@dataclass
class PromptContext:
    """Context for prompt generation."""

    query: str
    domain: Domain = Domain.GENERAL
    task_type: TaskType = TaskType.RESEARCH
    depth: int = 2  # 1=shallow, 3=deep
    audience: str = "expert"  # "expert", "general", "executive"
    constraints: list[str] = field(default_factory=list)

    # Session context
    session_summary: str = ""
    previous_findings: list[str] = field(default_factory=list)

    # Output preferences
    output_format: str = "markdown"  # "markdown", "json", "bullet"
    max_length: int = 0  # 0 = no limit

    # Knowledge context (injected by KnowledgeRetriever at runtime)
    knowledge_context: str = ""


@dataclass
class GeneratedPrompt:
    """A generated system prompt with metadata."""

    prompt: str
    domain: Domain
    task_type: TaskType
    version: str
    generated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def hash(self) -> str:
        return hashlib.md5(self.prompt.encode()).hexdigest()[:8]


# =============================================================================
# Domain Templates
# =============================================================================

# =============================================================================
# Domain Templates & Task Modifiers (Loaded from Config)
# =============================================================================

# Default fallbacks in case config is missing (Minimal set)
DEFAULT_DOMAIN_TEMPLATES = {
    Domain.GENERAL: """You are a versatile research analyst.
Verify claims, note credibility, and structure findings logically."""
}

DEFAULT_TASK_MODIFIERS = {TaskType.RESEARCH: "Focus on comprehensive investigation."}


def load_prompts_config() -> tuple[dict, dict, dict, dict]:
    """Load templates from configs/prompts.yaml.

    Returns:
        (domain_templates, task_modifiers, depth_instructions, audience_instructions)
    """
    from pathlib import Path

    import yaml

    try:
        # Resolve path relative to project root
        root_path = Path(__file__).resolve().parents[3]
        config_path = root_path / "configs" / "prompts.yaml"

        if not config_path.exists():
            logger.warning(f"Prompts config not found at {config_path}")
            return {}, {}, {}, {}

        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Convert keys to Enum if possible
        domains = {}
        for k, v in data.get("domains", {}).items():
            try:
                # Match enum by value or name
                enum_key = None
                for d in Domain:
                    if d.value == k or d.name.lower() == k.lower():
                        enum_key = d
                        break
                if enum_key:
                    domains[enum_key] = v
            except Exception:
                pass

        tasks = {}
        for k, v in data.get("tasks", {}).items():
            try:
                enum_key = None
                for t in TaskType:
                    if t.value == k or t.name.lower() == k.lower():
                        enum_key = t
                        break
                if enum_key:
                    tasks[enum_key] = v
            except Exception:
                pass

        depth_instructions: dict = data.get("depth_instructions", {})
        audience_instructions: dict = data.get("audience_instructions", {})

        return domains, tasks, depth_instructions, audience_instructions

    except Exception as e:
        logger.error(f"Failed to load prompts config: {e}")
        return {}, {}, {}, {}


# =============================================================================
# Prompt Factory
# =============================================================================


class PromptFactory:
    """
    Generate specialized system prompts dynamically.

    Example:
        factory = PromptFactory()

        # Detect domain and generate prompt
        context = factory.analyze_query("What is Tesla's P/E ratio?")
        prompt = factory.generate(context)

        # Use with LLM
        response = await llm.generate(
            system_prompt=prompt.prompt,
            user_message=query,
        )
    """

    VERSION = "1.0.0"

    def __init__(self):
        self._domain_templates = DEFAULT_DOMAIN_TEMPLATES.copy()
        self._task_modifiers = DEFAULT_TASK_MODIFIERS.copy()

        # Load from config
        domains, tasks, depth_instructions, audience_instructions = load_prompts_config()
        self._domain_templates.update(domains)
        self._task_modifiers.update(tasks)
        self._depth_instructions: dict = depth_instructions
        self._audience_instructions: dict = audience_instructions

        # Load detection vocab
        from shared.vocab import load_vocab

        vocab = load_vocab("classification")
        self.domain_keywords = vocab.get("domains", {})
        self.task_keywords = vocab.get("task_types", {})

        logger.info(
            f"PromptFactory initialized with {len(self._domain_templates)} domains and {len(self._task_modifiers)} task modifiers"
        )

    def detect_domain(self, query: str) -> Domain:
        """Detect domain from query text."""
        query_lower = query.lower()

        # Check against loaded keywords
        for domain_name, keywords in self.domain_keywords.items():
            if any(kw in query_lower for kw in keywords):
                try:
                    # Finds matching enum by value
                    return Domain(domain_name)
                except ValueError:
                    pass

        return Domain.GENERAL

    def detect_task_type(self, query: str) -> TaskType:
        """Detect task type from query."""
        query_lower = query.lower()

        # Check against loaded keywords
        for task_name, keywords in self.task_keywords.items():
            if any(kw in query_lower for kw in keywords):
                try:
                    return TaskType(task_name)
                except ValueError:
                    pass

        return TaskType.RESEARCH

    def analyze_query(self, query: str) -> PromptContext:
        """Analyze query and create full context."""
        return PromptContext(
            query=query,
            domain=self.detect_domain(query),
            task_type=self.detect_task_type(query),
        )

    def generate(self, context: PromptContext) -> GeneratedPrompt:
        """Generate system prompt from context."""
        # Get domain template
        domain_template = self._domain_templates.get(
            context.domain, self._domain_templates[Domain.GENERAL]
        )

        # Get task modifier
        task_modifier = self._task_modifiers.get(context.task_type, "")

        # Build prompt
        parts = [domain_template]

        if task_modifier:
            parts.append(task_modifier)

        # Add depth instruction (loaded from configs/prompts.yaml depth_instructions)
        if context.depth >= 3:
            depth_key = "deep"
        elif context.depth <= 1:
            depth_key = "quick"
        else:
            depth_key = ""
        if depth_key:
            depth_text = self._depth_instructions.get(depth_key, "")
            if depth_text:
                parts.append(depth_text)

        # Add audience instruction (loaded from configs/prompts.yaml audience_instructions)
        audience_text = self._audience_instructions.get(context.audience or "", "")
        if audience_text:
            parts.append(audience_text)

        # Add session context if available
        if context.session_summary:
            parts.append(f"""
Session Context:
{context.session_summary}""")

        if context.previous_findings:
            findings = "\n".join(f"- {f}" for f in context.previous_findings[-5:])
            parts.append(f"""
Previous Findings:
{findings}""")

        # Add constraints
        if context.constraints:
            constraints = "\n".join(f"- {c}" for c in context.constraints)
            parts.append(f"""
Constraints:
{constraints}""")

        # Add output format
        if context.output_format == "json":
            parts.append("""
Output: Return response as valid JSON.""")
        elif context.output_format == "bullet":
            parts.append("""
Output: Use bullet points for clarity.""")

        # Add retrieved knowledge context (domain expertise from knowledge library)
        if context.knowledge_context:
            parts.append(context.knowledge_context)

        prompt = "\n\n".join(parts)

        return GeneratedPrompt(
            prompt=prompt,
            domain=context.domain,
            task_type=context.task_type,
            version=self.VERSION,
        )

    def register_domain(self, domain: Domain, template: str) -> None:
        """Register or update a domain template."""
        self._domain_templates[domain] = template
        logger.info(f"Registered domain template: {domain.value}")

    def register_task_modifier(self, task_type: TaskType, modifier: str) -> None:
        """Register or update a task modifier."""
        self._task_modifiers[task_type] = modifier
        logger.info(f"Registered task modifier: {task_type.value}")

    async def generate_with_knowledge(self, context: PromptContext) -> GeneratedPrompt:
        """
        Generate system prompt with dynamic knowledge retrieval.

        Retrieves relevant skills and rules from the knowledge registry
        and injects them into the prompt context before generation.
        """
        try:
            from shared.knowledge.retriever import get_knowledge_retriever

            retriever = get_knowledge_retriever()
            knowledge_context = await retriever.retrieve_all(
                query=context.query,
                skill_limit=3,
                rule_limit=2,
                domain=context.domain.value if context.domain != Domain.GENERAL else None,
            )
            if knowledge_context:
                context.knowledge_context = knowledge_context
                logger.info(
                    f"PromptFactory: Injected knowledge context "
                    f"({len(knowledge_context)} chars) for domain={context.domain.value}"
                )
        except Exception as e:
            logger.debug(f"PromptFactory: Knowledge retrieval skipped ({e})")

        return self.generate(context)


# Global instance
_factory: PromptFactory | None = None


def get_prompt_factory() -> PromptFactory:
    """Get or create global prompt factory."""
    global _factory
    if _factory is None:
        _factory = PromptFactory()
    return _factory


def generate_prompt(query: str, **kwargs) -> GeneratedPrompt:
    """Convenience function to generate prompt for query."""
    factory = get_prompt_factory()
    context = factory.analyze_query(query)

    # Override with kwargs
    for key, value in kwargs.items():
        if hasattr(context, key):
            setattr(context, key, value)

    return factory.generate(context)


async def generate_prompt_with_knowledge(query: str, **kwargs) -> GeneratedPrompt:
    """Convenience function to generate prompt with knowledge retrieval."""
    factory = get_prompt_factory()
    context = factory.analyze_query(query)

    for key, value in kwargs.items():
        if hasattr(context, key):
            setattr(context, key, value)

    return await factory.generate_with_knowledge(context)
