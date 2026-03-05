"""
Tier 8 Team Orchestrator — Types.

Pydantic models for sprint-based execution: sprints, sprint results,
mission results, sprint reviews, and the corporate OODA loop outcome.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ============================================================================
# Sprint Planning
# ============================================================================


class Sprint(BaseModel):
    """A group of parallel tasks with a shared dependency level.

    Sprint N contains all MissionChunks whose dependencies are
    satisfied by the outputs of Sprints 1..N-1.
    """

    sprint_id: str = Field(..., description="Unique sprint identifier")
    sprint_number: int = Field(
        ..., ge=1, description="Sequential sprint number (1-based)"
    )
    mission_id: str = Field(..., description="Parent mission ID")
    objective: str = Field(
        ..., description="High-level sprint objective"
    )
    chunks: list[Any] = Field(
        default_factory=list,
        description="MissionChunks parallelizable within this sprint",
    )
    depends_on_sprint_ids: list[str] = Field(
        default_factory=list,
        description="Sprint IDs that must complete before this one",
    )
    estimated_duration_ms: float = Field(
        default=0.0, ge=0.0, description="Estimated wall-clock duration"
    )


# ============================================================================
# Sprint Execution Results
# ============================================================================


class SprintResult(BaseModel):
    """Outcome of a single sprint execution."""

    sprint_id: str = Field(..., description="Matching sprint ID")
    completed_chunks: list[str] = Field(
        default_factory=list, description="chunk_ids that succeeded"
    )
    failed_chunks: list[str] = Field(
        default_factory=list, description="chunk_ids that failed"
    )
    agent_results: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="agent_id → CorporateAgentProcessResponse (serialized)",
    )
    artifacts_produced: list[str] = Field(
        default_factory=list, description="Vault artifact IDs produced"
    )
    total_cost: float = Field(default=0.0, ge=0.0)
    duration_ms: float = Field(default=0.0, ge=0.0)
    was_checkpointed: bool = Field(default=False)


# ============================================================================
# Sprint Review (Post-Sprint Retrospective)
# ============================================================================


class SprintReview(BaseModel):
    """Post-sprint retrospective produced by T3 reflection.

    This is the corporate equivalent of an individual kernel's
    post-execution reflection, but scoped to an entire sprint.
    """

    sprint_id: str = Field(..., description="Sprint being reviewed")
    quality_assessment: str = Field(
        default="",
        description="From T3 critique_execution() — narrative evaluation",
    )
    issues_found: list[str] = Field(
        default_factory=list, description="Problems detected during review"
    )
    new_backlog_items: list[str] = Field(
        default_factory=list,
        description="Discovered work to add to future sprints",
    )
    next_sprint_approved: bool = Field(
        default=True,
        description="From T3 run_pre_execution_check() — conscience gate",
    )


# ============================================================================
# Mission-Level Aggregation
# ============================================================================


class MissionResult(BaseModel):
    """Aggregated outcome from all sprints in a mission."""

    mission_id: str = Field(..., description="Unique mission identifier")
    total_sprints: int = Field(default=0, ge=0)
    completed_sprints: int = Field(default=0, ge=0)
    all_artifacts: list[str] = Field(
        default_factory=list, description="All Vault artifact IDs"
    )
    all_agent_results: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="agent_id → CorporateAgentProcessResponse (serialized)",
    )
    total_cost: float = Field(default=0.0, ge=0.0)
    total_duration_ms: float = Field(default=0.0, ge=0.0)
    completion_pct: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Fraction of sprints completed",
    )
    final_review: SprintReview | None = Field(
        default=None, description="Review from the final sprint"
    )


# ============================================================================
# Corporate OODA Loop Result
# ============================================================================


class CorporateOODAResult(BaseModel):
    """Result of the corporate HTTP monitoring loop.

    Tracks how many polling cycles occurred and what actions
    the corporate OODA loop took during sprint execution.
    """

    total_cycles: int = Field(default=0, ge=0)
    termination_reason: str = Field(
        default="all_complete",
        description="all_complete | escalated | aborted | budget_exhausted",
    )
    events_processed: int = Field(default=0, ge=0)
    handoffs_executed: int = Field(default=0, ge=0)
    agents_fired: int = Field(default=0, ge=0)
    agents_hired: int = Field(default=0, ge=0)
    checkpoints_saved: int = Field(default=0, ge=0)
