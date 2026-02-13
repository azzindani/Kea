"""
Structured LLM Output Schemas.

Pydantic models that define the exact expected output structure for every type
of LLM inference call in the kernel. Replaces freeform text parsing with
validated, typed, predictable output.

Each schema is used with structured output / JSON mode to ensure the LLM
returns data that can be reliably consumed by the orchestration pipeline.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


# ============================================================================
# Planner Output
# ============================================================================


class SubTask(BaseModel):
    """A single decomposed subtask produced by the planner."""

    id: str = Field(description="Unique subtask identifier")
    description: str = Field(description="What this subtask accomplishes")
    domain: str = Field(default="general", description="Domain: finance, technology, etc.")
    required_tools: list[str] = Field(
        default_factory=list,
        description="Tool names needed for this subtask",
    )
    depends_on: list[str] = Field(
        default_factory=list,
        description="IDs of subtasks this depends on",
    )
    estimated_complexity: Literal["trivial", "simple", "moderate", "complex"] = Field(
        default="moderate",
        description="How complex this subtask is",
    )
    expected_output: str = Field(
        default="",
        description="What the output of this subtask should look like",
    )


class PlannerOutput(BaseModel):
    """Structured output from the planner node."""

    understanding: str = Field(description="What the planner understood from the query")
    strategy: str = Field(description="High-level approach to solving the query")
    subtasks: list[SubTask] = Field(description="Decomposed subtasks")
    execution_order: list[list[str]] = Field(
        description="Phases of execution: [[parallel IDs], [next phase IDs], ...]",
    )
    risks: list[str] = Field(default_factory=list, description="Identified risks")
    estimated_total_tools: int = Field(
        default=0,
        description="Estimated total tool calls needed across all subtasks",
    )
    requires_delegation: bool = Field(
        default=False,
        description="Whether this plan requires delegation to child cells",
    )


# ============================================================================
# Reasoning Step Output
# ============================================================================


class ActionType(str, Enum):
    """Actions available to a kernel cell during reasoning."""

    CALL_TOOL = "call_tool"
    ANALYZE = "analyze"
    SYNTHESIZE = "synthesize"
    DELEGATE = "delegate"
    ESCALATE = "escalate"
    CONSULT = "consult"
    COMPLETE = "complete"


class ReasoningOutput(BaseModel):
    """Structured output from each reasoning step in the ReAct loop."""

    thought: str = Field(description="Chain-of-thought reasoning")
    action: ActionType = Field(description="What action to take")
    action_input: dict[str, Any] = Field(
        default_factory=dict,
        description="Typed input for the chosen action",
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in this decision",
    )
    rationale: str = Field(default="", description="Why this action was chosen")

    # For delegation
    delegate_to: str | None = Field(
        default=None,
        description="Role to delegate to (e.g., 'financial_analyst')",
    )
    delegation_context: str | None = Field(
        default=None,
        description="Additional context for the delegated agent",
    )


# ============================================================================
# Critic Output
# ============================================================================


class CriticOutput(BaseModel):
    """Structured output from the critic agent."""

    overall_assessment: Literal["strong", "adequate", "weak", "reject"] = Field(
        description="Overall quality assessment",
    )

    dimension_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Per-dimension scores: {accuracy: 0.8, completeness: 0.7, ...}",
    )

    strengths: list[str] = Field(default_factory=list, description="What was done well")
    weaknesses: list[str] = Field(default_factory=list, description="What needs improvement")

    missing_information: list[str] = Field(
        default_factory=list,
        description="Specific data gaps identified",
    )
    factual_concerns: list[str] = Field(
        default_factory=list,
        description="Potential inaccuracies or unsupported claims",
    )

    suggestions: list[str] = Field(
        default_factory=list,
        description="Concrete improvement suggestions",
    )
    requires_revision: bool = Field(
        default=False,
        description="Whether the output needs revision before it can proceed",
    )


# ============================================================================
# Judge Output
# ============================================================================


class JudgeOutput(BaseModel):
    """Structured output from the judge agent."""

    verdict: Literal["accept", "revise", "reject", "escalate"] = Field(
        description="Final judgment on the output quality",
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Judge's confidence in the verdict",
    )

    quality_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Multi-dimensional quality scores",
    )

    reasoning: str = Field(default="", description="Why this verdict was reached")
    revision_instructions: str | None = Field(
        default=None,
        description="If verdict is 'revise', what specifically to fix",
    )

    final_answer: str | None = Field(
        default=None,
        description="The judge's approved final answer (if accepted)",
    )

    contribution_assessment: dict[str, float] = Field(
        default_factory=dict,
        description="Assessment of contribution quality per source: {source: weight}",
    )


# ============================================================================
# Synthesis Output
# ============================================================================


class SectionOutput(BaseModel):
    """A section of the synthesized report."""

    title: str
    content: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    sources: list[str] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)


class SynthesisOutput(BaseModel):
    """Structured output from the synthesizer."""

    executive_summary: str = Field(description="2-3 sentence executive summary")
    sections: list[SectionOutput] = Field(description="Report sections")
    key_findings: list[str] = Field(description="Top findings")
    recommendations: list[str] = Field(default_factory=list, description="Actionable recommendations")
    overall_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall confidence in the synthesis",
    )
    caveats: list[str] = Field(default_factory=list, description="Important caveats")
    methodology_note: str = Field(default="", description="How the analysis was conducted")


# ============================================================================
# Complexity Assessment Output
# ============================================================================


class ProcessingMode(str, Enum):
    """How a kernel cell should process a task."""

    DIRECT = "direct"       # Trivial: respond immediately, no tools
    SOLO = "solo"           # Simple/Moderate: single agent with tools
    DELEGATE = "delegate"   # Complex: spawn child cells
    HIERARCHY = "hierarchy"  # Enterprise: multi-level hierarchy


class ComplexityAssessment(BaseModel):
    """Structured assessment of task complexity."""

    tier: Literal["trivial", "simple", "moderate", "complex", "enterprise"] = Field(
        description="Complexity tier of the task",
    )
    processing_mode: ProcessingMode = Field(
        description="How this task should be processed",
    )
    estimated_tools: int = Field(
        default=0,
        description="Estimated number of tool calls needed",
    )
    estimated_depth: int = Field(
        default=0,
        description="Estimated delegation depth needed",
    )
    estimated_agents: int = Field(
        default=1,
        description="Estimated number of agents needed",
    )
    rationale: str = Field(default="", description="Why this assessment was made")


# ============================================================================
# Role Resolution Output
# ============================================================================


class RoleResolution(BaseModel):
    """Structured output from role resolution for delegation."""

    role_name: str = Field(description="Name of the role: e.g., 'senior_financial_analyst'")
    domain: str = Field(description="Domain this role belongs to")
    required_skills: list[str] = Field(
        default_factory=list,
        description="Skill identifiers to retrieve from knowledge registry",
    )
    tool_patterns: list[str] = Field(
        default_factory=list,
        description="Tool name patterns this role needs access to",
    )
    quality_bar: Literal["draft", "professional", "executive"] = Field(
        default="professional",
        description="Expected output quality from this role",
    )
# ============================================================================
# Artifact Models (Phase 5)
# ============================================================================


class ArtifactType(str, Enum):
    """Types of work products produced by the kernel."""

    REPORT = "report"           # Formal written report
    ANALYSIS = "analysis"       # Analytical finding or evaluation
    DATASET = "dataset"         # Structured data (CSV, JSON, etc.)
    SUMMARY = "summary"         # Executive or technical summary
    CODE = "code"               # Scripts, queries, or snippets
    RECOMMENDATION = "recommendation"  # Actionable recommendation
    MEMO = "memo"               # Internal or informal communication


class ArtifactStatus(str, Enum):
    """Lifecycle states of an artifact."""

    DRAFT = "draft"             # Work in progress
    REVIEW = "review"           # Pending parent/peer review
    REVISION = "revision"       # Sent back for improvement
    APPROVED = "approved"       # Quality gate passed
    PUBLISHED = "published"     # Final version ready for delivery


class ArtifactMetadata(BaseModel):
    """Metadata for a single artifact."""

    sources: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)
    confidence_breakdown: dict[str, float] = Field(default_factory=list)


class Artifact(BaseModel):
    """A structured work product with a lifecycle."""

    id: str = Field(description="Unique artifact identifier")
    type: ArtifactType = Field(description="Artifact category")
    title: str = Field(description="Display title")
    summary: str = Field(default="", description="Short summary/abstract")
    content: str = Field(description="The actual work product content")
    status: ArtifactStatus = Field(default=ArtifactStatus.DRAFT)
    version: int = Field(default=1)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: ArtifactMetadata = Field(default_factory=ArtifactMetadata)

    # Lineage
    parent_id: str | None = Field(default=None, description="ID of artifact this was derived from")
    cell_id: str | None = Field(default=None, description="ID of the cell that produced this")
    produced_at: str | None = Field(default=None, description="ISO timestamp")


class WorkPackage(BaseModel):
    """The final structured output from a kernel cell."""

    summary: str = Field(description="Executive summary of the entire work package")
    artifacts: list[Artifact] = Field(default_factory=list)
    overall_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    key_findings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
