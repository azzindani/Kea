"""
Tier 2 Task Decomposition — Types.

Pydantic models for goal decomposition into structured sub-tasks
with dependency graphs and skill mappings.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

# ============================================================================
# World State (Input Context)
# ============================================================================


class WorldState(BaseModel):
    """Current agent world state containing the high-level goal.

    This is the universal context object passed to all T2 engines.
    """

    goal: str = Field(..., description="High-level natural language goal")
    context: dict[str, str] = Field(
        default_factory=dict,
        description="Additional context (session, user info, etc.)",
    )
    available_skills: list[str] = Field(
        default_factory=list,
        description="Skills available to the agent",
    )
    available_tools: list[str] = Field(
        default_factory=list,
        description="MCP tools available for execution",
    )
    knowledge_domains: list[str] = Field(
        default_factory=list,
        description="Knowledge domains loaded for this agent",
    )


# ============================================================================
# Complexity Assessment
# ============================================================================


class ComplexityLevel(StrEnum):
    """Goal complexity categories."""

    ATOMIC = "atomic"           # Single-step, single-skill
    COMPOUND = "compound"       # Multi-step, single-domain
    MULTI_DOMAIN = "multi_domain"  # Multi-step, cross-domain


class ComplexityAssessment(BaseModel):
    """Result of goal complexity analysis."""

    level: ComplexityLevel = Field(..., description="Assessed complexity")
    estimated_sub_tasks: int = Field(default=1, ge=1)
    primary_intent: str = Field(default="", description="From T1 intent detection")
    entity_count: int = Field(default=0, ge=0, description="Number of entities detected")
    domains_involved: list[str] = Field(
        default_factory=list,
        description="Knowledge domains needed",
    )
    goal_description: str = Field(default="", description="The original natural language goal")
    reasoning: str = Field(default="", description="Why this complexity level was chosen")


# ============================================================================
# Sub-Goals & Dependencies
# ============================================================================


class SubGoal(BaseModel):
    """A logical sub-goal split from the main goal."""

    id: str = Field(..., description="Unique sub-goal identifier")
    description: str = Field(..., description="Natural language sub-goal")
    domain: str = Field(default="general", description="Knowledge domain")
    inputs: list[str] = Field(
        default_factory=list,
        description="Required input variable names",
    )
    outputs: list[str] = Field(
        default_factory=list,
        description="Produced output variable names",
    )


class DependencyEdge(BaseModel):
    """A dependency between two sub-goals."""

    from_id: str = Field(..., description="Source sub-goal ID (must complete first)")
    to_id: str = Field(..., description="Target sub-goal ID (depends on source)")
    data_flow: str = Field(default="", description="What data flows between them")


class DependencyGraph(BaseModel):
    """Directed graph of sub-goal dependencies."""

    nodes: list[str] = Field(default_factory=list, description="Sub-goal IDs")
    edges: list[DependencyEdge] = Field(default_factory=list)
    parallel_groups: list[list[str]] = Field(
        default_factory=list,
        description="Groups of sub-goals that can run in parallel",
    )
    execution_order: list[str] = Field(
        default_factory=list,
        description="Topologically sorted execution order",
    )


# ============================================================================
# Output: SubTaskItem
# ============================================================================


class SubTaskItem(BaseModel):
    """A fully annotated sub-task ready for Tier 3 Graph Synthesizer.

    This is the primary output consumed by the DAG assembly layer.
    """

    id: str = Field(..., description="Unique task identifier")
    description: str = Field(..., description="What this task does")
    domain: str = Field(default="general")
    required_skills: list[str] = Field(
        default_factory=list,
        description="Agent skills needed",
    )
    required_tools: list[str] = Field(
        default_factory=list,
        description="MCP tool categories needed",
    )
    depends_on: list[str] = Field(
        default_factory=list,
        description="IDs of tasks this depends on",
    )
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    parallelizable: bool = Field(
        default=False,
        description="Whether this can run in parallel with other tasks",
    )
