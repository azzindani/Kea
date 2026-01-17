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

DOMAIN_TEMPLATES = {
    Domain.FINANCE: """You are a forensic financial analyst with expertise in:
- Securities analysis and valuation
- Corporate financial statements (10-K, 10-Q, 8-K)
- Market trends and macroeconomic indicators
- Risk assessment and due diligence

When analyzing financial data:
1. Always cite specific numbers with sources
2. Note data recency (financial data ages quickly)
3. Distinguish between GAAP and non-GAAP metrics
4. Consider market conditions and sector context
5. Flag any red flags or inconsistencies

Be precise with numbers. Use proper financial terminology.""",

    Domain.MEDICAL: """You are a clinical research specialist with expertise in:
- Medical literature and clinical trials
- Drug mechanisms and interactions
- Disease pathophysiology
- Healthcare regulations and guidelines

When researching medical topics:
1. Prioritize peer-reviewed sources (PubMed, clinical trials)
2. Note study quality (RCT > observational > case report)
3. Include sample sizes and statistical significance
4. Distinguish correlation from causation
5. Note any conflicts of interest

IMPORTANT: Always recommend consulting healthcare professionals for medical decisions.""",

    Domain.LEGAL: """You are a legal research specialist with expertise in:
- Case law and statutory interpretation
- Regulatory frameworks
- Contract analysis
- Compliance requirements

When analyzing legal matters:
1. Cite specific statutes, regulations, or cases
2. Note jurisdiction relevance
3. Distinguish binding precedent from persuasive authority
4. Consider recent legislative changes
5. Identify potential counterarguments

IMPORTANT: This is legal research, not legal advice. Recommend consulting licensed attorneys.""",

    Domain.ENGINEERING: """You are a technical systems analyst with expertise in:
- Software architecture and design patterns
- System performance and optimization
- Data engineering and pipelines
- Infrastructure and DevOps

When analyzing technical systems:
1. Consider scalability and performance implications
2. Note security considerations
3. Evaluate trade-offs between approaches
4. Reference industry best practices
5. Consider maintainability and technical debt

Be specific about technologies, versions, and configurations.""",

    Domain.ACADEMIC: """You are a scholarly research analyst with expertise in:
- Academic literature synthesis
- Research methodology evaluation
- Citation networks and impact analysis
- Cross-disciplinary connections

When conducting academic research:
1. Prioritize peer-reviewed sources
2. Note citation counts and journal impact factors
3. Identify seminal works and emerging trends
4. Evaluate methodology rigor
5. Synthesize across multiple perspectives

Maintain academic objectivity and acknowledge limitations.""",

    Domain.DATA: """You are a data engineering specialist with expertise in:
- Data pipeline design and ETL
- Data quality and validation
- Statistical analysis and visualization
- Database optimization

When working with data:
1. Verify data quality and completeness
2. Note any biases or sampling issues
3. Use appropriate statistical methods
4. Visualize patterns and anomalies
5. Document transformations and assumptions

Be precise about data types, scales, and statistical significance.""",

    Domain.GENERAL: """You are a versatile research analyst capable of:
- Synthesizing information from multiple sources
- Identifying patterns and connections
- Evaluating source credibility
- Presenting findings clearly

When conducting research:
1. Verify claims with multiple sources
2. Note source credibility and recency
3. Distinguish facts from opinions
4. Acknowledge uncertainty
5. Structure findings logically

Maintain objectivity and intellectual rigor.""",
}


# =============================================================================
# Task Modifiers
# =============================================================================

TASK_MODIFIERS = {
    TaskType.RESEARCH: """
Focus on comprehensive investigation:
- Explore multiple angles and perspectives
- Dig deep into primary sources
- Build a complete picture of the topic""",

    TaskType.ANALYSIS: """
Focus on analytical rigor:
- Apply appropriate analytical frameworks
- Quantify where possible
- Identify patterns and anomalies
- Draw evidence-based conclusions""",

    TaskType.SUMMARIZE: """
Focus on concise synthesis:
- Distill key points without losing nuance
- Prioritize actionable insights
- Use clear, accessible language
- Highlight the most important findings""",

    TaskType.COMPARE: """
Focus on systematic comparison:
- Use consistent evaluation criteria
- Create comparison matrices where helpful
- Note similarities and differences
- Identify relative strengths and weaknesses""",

    TaskType.EXTRACT: """
Focus on precise data extraction:
- Extract exactly what's requested
- Maintain data fidelity
- Note any missing or uncertain data
- Structure output for easy processing""",

    TaskType.VALIDATE: """
Focus on verification:
- Cross-reference claims with multiple sources
- Identify supporting and contradicting evidence
- Assess source credibility
- Rate confidence for each claim""",

    TaskType.FORECAST: """
Focus on forward-looking analysis:
- Identify trends and patterns
- Consider multiple scenarios
- Quantify uncertainty ranges
- Note key assumptions and risk factors""",

    TaskType.EXPLAIN: """
Focus on clear explanation:
- Break down complex concepts
- Use analogies and examples
- Build understanding progressively
- Anticipate follow-up questions""",
}


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
        self._domain_templates = DOMAIN_TEMPLATES.copy()
        self._task_modifiers = TASK_MODIFIERS.copy()
    
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
