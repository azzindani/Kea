"""
Tier 3 Advanced Planning — Types.

Pydantic models for DAG sequencing, tool binding, hypothesis generation,
and progress tracking.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

# ============================================================================
# Planning Constraints (Input)
# ============================================================================


class PriorityMode(StrEnum):
    """Routing strategy for sequencing sub-tasks."""

    SPEED = "speed"         # Minimize wall-clock time (max parallelism)
    COST = "cost"           # Minimize resource consumption
    FIDELITY = "fidelity"   # Maximize accuracy/quality
    BALANCED = "balanced"   # Config-driven weighted blend


class PlanningConstraints(BaseModel):
    """Constraints governing the planning pipeline."""

    priority_mode: PriorityMode = Field(
        default=PriorityMode.BALANCED,
        description="Routing strategy for sub-task ordering",
    )
    max_parallel_nodes: int = Field(
        default=4,
        ge=1,
        description="Maximum concurrent node executions",
    )
    budget_limit: float = Field(
        default=0.0,
        ge=0.0,
        description="Maximum resource cost (0 = unlimited)",
    )
    deadline_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Maximum wall-clock time in ms (0 = unlimited)",
    )
    required_tools: list[str] = Field(
        default_factory=list,
        description="MCP tools that must be available",
    )
    quality_bar: float = Field(default=0.7, ge=0.0, le=1.0)
    allowed_tools: list[str] = Field(default_factory=list)
    forbidden_actions: list[str] = Field(default_factory=list)


# ============================================================================
# Sequenced Task (Step 1 output)
# ============================================================================


class SequencedTask(BaseModel):
    """A sub-task annotated with sequencing metadata."""

    task_id: str = Field(..., description="Originating SubTaskItem ID")
    description: str = Field(..., description="Task description")
    priority_rank: int = Field(
        default=0,
        ge=0,
        description="Execution priority (lower = higher priority)",
    )
    estimated_cost: float = Field(
        default=0.0,
        ge=0.0,
        description="Estimated resource cost for this task",
    )
    estimated_duration_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Estimated execution time in ms",
    )
    parallelizable: bool = Field(default=False)
    depends_on: list[str] = Field(default_factory=list)
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    domain: str = Field(default="general")
    required_skills: list[str] = Field(default_factory=list)
    required_tools: list[str] = Field(default_factory=list)


# ============================================================================
# Bound Task (Step 2 output)
# ============================================================================


class MCPToolBinding(BaseModel):
    """A resolved binding between a task and an MCP tool."""

    tool_id: str = Field(..., description="MCP tool identifier")
    tool_name: str = Field(..., description="Human-readable tool name")
    compatibility_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="How well this tool matches the task requirements",
    )


class MCPTool(BaseModel):
    """An MCP tool available in the registry, with full metadata."""

    tool_id: str = Field(..., description="MCP tool identifier")
    tool_name: str = Field(..., description="Human-readable tool name")
    description: str = Field(default="", description="What this tool does")
    compatibility_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Default compatibility score for this tool",
    )


class MCPToolRegistry(BaseModel):
    """Registry of available MCP tools for binding.

    Passed in by the caller (Tier 4 or Orchestrator service).
    """

    tools: list[MCPTool] = Field(
        default_factory=list,
        description="Available MCP tools",
    )


class BoundTask(BaseModel):
    """A sequenced task with MCP tool bindings resolved."""

    task_id: str = Field(...)
    description: str = Field(...)
    priority_rank: int = Field(default=0, ge=0)
    estimated_cost: float = Field(default=0.0, ge=0.0)
    estimated_duration_ms: float = Field(default=0.0, ge=0.0)
    parallelizable: bool = Field(default=False)
    depends_on: list[str] = Field(default_factory=list)
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    domain: str = Field(default="general")
    tool_binding: MCPToolBinding | None = Field(
        default=None,
        description="Resolved MCP tool for this task",
    )


# ============================================================================
# Expected Outcome / Hypothesis (Step 3 output)
# ============================================================================


class ExpectedOutcome(BaseModel):
    """A hypothesis about what a task should produce.

    Generated pre-execution, evaluated post-execution by the Reflection engine.
    """

    task_id: str = Field(..., description="Which task this expectation is for")
    description: str = Field(
        ...,
        description="Human-readable expectation (e.g., 'File should exist at path X')",
    )
    output_schema: str = Field(
        default="dict",
        description="Expected output Pydantic model name",
    )
    success_criteria: dict[str, Any] = Field(
        default_factory=dict,
        description="Key-value pairs defining success (e.g., {'status': 200})",
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Pre-execution confidence in this hypothesis",
    )


# ============================================================================
# Progress Tracker (Step 4 output)
# ============================================================================


class ProgressTracker(BaseModel):
    """Persistent state object that travels with the DAG through the OODA loop.

    Maps exactly how close the agent is to completing the overarching goal.
    """

    total_tasks: int = Field(default=0, ge=0)
    completed_tasks: int = Field(default=0, ge=0)
    failed_tasks: int = Field(default=0, ge=0)
    hypotheses_met: int = Field(default=0, ge=0)
    hypotheses_total: int = Field(default=0, ge=0)
    total_cost_consumed: float = Field(default=0.0, ge=0.0)
    completion_percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Overall progress as percentage",
    )


# ============================================================================
# Tracked Plan (Top-Level Output)
# ============================================================================


class TrackedPlan(BaseModel):
    """A fully planned, tool-bound, hypothesis-annotated execution plan.

    Ready for DAG compilation by the Graph Synthesizer.
    """

    plan_id: str = Field(..., description="Unique plan identifier")
    tasks: list[BoundTask] = Field(default_factory=list)
    hypotheses: list[ExpectedOutcome] = Field(default_factory=list)
    tracker: ProgressTracker = Field(default_factory=ProgressTracker)
    constraints: PlanningConstraints = Field(default_factory=PlanningConstraints)
