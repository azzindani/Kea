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
from typing import Any

from shared.logging import get_logger


logger = get_logger(__name__)


class Domain(str, Enum):
    """Research domains."""
    RESEARCH = "research"
    FINANCE = "finance"
    MEDICAL = "medical"
    LEGAL = "legal"
    ENGINEERING = "engineering"
    ACADEMIC = "academic"
    DATA = "data"
    GENERAL = "general"


class TaskType(str, Enum):
    """Task types requiring different approaches."""
    RESEARCH = "research"           # Deep investigation
    ANALYSIS = "analysis"           # Data analysis
    SUMMARIZE = "summarize"         # Condensing information
    COMPARE = "compare"             # Comparison of entities
    EXTRACT = "extract"             # Extract specific data
    VALIDATE = "validate"           # Fact-checking
    FORECAST = "forecast"           # Predictions
    EXPLAIN = "explain"             # Explanations


@dataclass
class PromptContext:
    """Context for prompt generation."""
    query: str
    domain: Domain = Domain.GENERAL
    task_type: TaskType = TaskType.RESEARCH
    depth: int = 2                  # 1=shallow, 3=deep
    audience: str = "expert"        # "expert", "general", "executive"
    constraints: list[str] = field(default_factory=list)
    
    # Session context
    session_summary: str = ""
    previous_findings: list[str] = field(default_factory=list)
    
    # Output preferences
    output_format: str = "markdown"  # "markdown", "json", "bullet"
    max_length: int = 0              # 0 = no limit


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

DEFAULT_TASK_MODIFIERS = {
    TaskType.RESEARCH: "Focus on comprehensive investigation."
}

def load_prompts_config() -> tuple[dict, dict]:
    """Load templates from configs/prompts.yaml."""
    import yaml
    from pathlib import Path
    
    try:
        # Resolve path relative to project root
        root_path = Path(__file__).resolve().parents[3]
        config_path = root_path / "configs" / "prompts.yaml"
        
        if not config_path.exists():
            logger.warning(f"Prompts config not found at {config_path}")
            return {}, {}
            
        with open(config_path, "r", encoding="utf-8") as f:
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
                
        return domains, tasks
        
    except Exception as e:
        logger.error(f"Failed to load prompts config: {e}")
        return {}, {}



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
        domains, tasks = load_prompts_config()
        self._domain_templates.update(domains)
        self._task_modifiers.update(tasks)
        
        logger.info(f"PromptFactory initialized with {len(self._domain_templates)} domains and {len(self._task_modifiers)} task modifiers")
    
    def detect_domain(self, query: str) -> Domain:
        """Detect domain from query text."""
        query_lower = query.lower()
        
        # Finance indicators
        if any(kw in query_lower for kw in [
            "stock", "revenue", "profit", "market cap", "p/e", "earnings",
            "investment", "dividend", "financial", "trading", "valuation",
            "sec filing", "10-k", "10-q", "balance sheet", "cash flow"
        ]):
            return Domain.FINANCE
        
        # Medical indicators
        if any(kw in query_lower for kw in [
            "disease", "treatment", "drug", "clinical", "patient", "symptom",
            "diagnosis", "therapy", "medical", "health", "pharma", "fda",
            "trial", "efficacy", "side effect", "dosage"
        ]):
            return Domain.MEDICAL
        
        # Legal indicators
        if any(kw in query_lower for kw in [
            "law", "legal", "regulation", "statute", "court", "case",
            "contract", "compliance", "liability", "rights", "patent",
            "trademark", "litigation", "sue", "judgment"
        ]):
            return Domain.LEGAL
        
        # Engineering indicators
        if any(kw in query_lower for kw in [
            "code", "software", "system", "architecture", "api", "database",
            "performance", "scalability", "infrastructure", "deploy",
            "algorithm", "optimize", "technical", "engineering"
        ]):
            return Domain.ENGINEERING
        
        # Academic indicators
        if any(kw in query_lower for kw in [
            "research", "study", "paper", "journal", "peer-review",
            "methodology", "hypothesis", "experiment", "thesis",
            "publication", "citation", "academic"
        ]):
            return Domain.ACADEMIC
        
        # Data indicators
        if any(kw in query_lower for kw in [
            "data", "dataset", "analysis", "statistics", "correlation",
            "trend", "visualization", "etl", "pipeline", "query"
        ]):
            return Domain.DATA
        
        return Domain.GENERAL
    
    def detect_task_type(self, query: str) -> TaskType:
        """Detect task type from query."""
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in ["compare", "versus", "vs", "difference"]):
            return TaskType.COMPARE
        
        if any(kw in query_lower for kw in ["summarize", "summary", "brief", "overview"]):
            return TaskType.SUMMARIZE
        
        if any(kw in query_lower for kw in ["extract", "get", "list all", "find all"]):
            return TaskType.EXTRACT
        
        if any(kw in query_lower for kw in ["verify", "check", "validate", "is it true"]):
            return TaskType.VALIDATE
        
        if any(kw in query_lower for kw in ["predict", "forecast", "future", "will"]):
            return TaskType.FORECAST
        
        if any(kw in query_lower for kw in ["explain", "why", "how does", "what is"]):
            return TaskType.EXPLAIN
        
        if any(kw in query_lower for kw in ["analyze", "analysis", "examine"]):
            return TaskType.ANALYSIS
        
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
            context.domain,
            self._domain_templates[Domain.GENERAL]
        )
        
        # Get task modifier
        task_modifier = self._task_modifiers.get(
            context.task_type,
            ""
        )
        
        # Build prompt
        parts = [domain_template]
        
        if task_modifier:
            parts.append(task_modifier)
        
        # Add depth instruction
        if context.depth >= 3:
            parts.append("""
Research Depth: DEEP
- Leave no stone unturned
- Explore edge cases and exceptions
- Trace claims to primary sources""")
        elif context.depth <= 1:
            parts.append("""
Research Depth: QUICK
- Focus on key facts only
- Prioritize speed over completeness
- Use cached/known information when appropriate""")
        
        # Add audience instruction
        if context.audience == "executive":
            parts.append("""
Audience: Executive
- Lead with conclusions and recommendations
- Keep technical details minimal
- Focus on business implications""")
        elif context.audience == "general":
            parts.append("""
Audience: General
- Avoid jargon, explain technical terms
- Use analogies for complex concepts
- Keep language accessible""")
        
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
