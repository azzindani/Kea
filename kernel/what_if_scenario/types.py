"""
Tier 2 What-If Scenario — Types.

Pydantic models for offline counter-factual simulation
and risk/reward analysis before live execution.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class VerdictDecision(StrEnum):
    """Simulation outcome decision."""

    APPROVE = "approve"     # Risk acceptable, proceed
    REJECT = "reject"       # Risk too high, request alternative
    MODIFY = "modify"       # Moderate risk, append safeguards


class OutcomeBranch(BaseModel):
    """A single simulated outcome branch (success or failure path)."""

    branch_id: str = Field(..., description="Unique branch identifier")
    description: str = Field(..., description="What happens in this branch")
    is_success: bool = Field(..., description="Whether this is a success path")
    likelihood: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Estimated probability of this branch",
    )
    terminal_state: str = Field(
        default="",
        description="Description of the end state",
    )
    path_steps: list[str] = Field(
        default_factory=list,
        description="Steps taken in this branch",
    )


class ConsequencePrediction(BaseModel):
    """Predicted environmental side effects for an outcome branch."""

    branch_id: str = Field(..., description="Which branch this predicts for")
    resource_impact: str = Field(
        default="low",
        description="Resource consumption estimate (low, medium, high)",
    )
    state_mutations: list[str] = Field(
        default_factory=list,
        description="State changes that would occur",
    )
    reversible: bool = Field(
        default=True,
        description="Whether the action can be undone",
    )
    severity_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Severity of negative consequences",
    )
    external_impacts: list[str] = Field(
        default_factory=list,
        description="Effects on external services/systems",
    )


class SimulationVerdict(BaseModel):
    """Final verdict from the What-If simulation engine."""

    decision: VerdictDecision = Field(..., description="Approve, Reject, or Modify")
    risk_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Aggregate risk score (0=safe, 1=dangerous)",
    )
    reward_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Expected reward/benefit score",
    )
    reasoning: str = Field(..., description="Human-readable explanation of the verdict")
    safeguards: list[str] = Field(
        default_factory=list,
        description="Recommended safeguards (for MODIFY verdict)",
    )
    branches_analyzed: int = Field(default=0, ge=0)


class CompiledDAG(BaseModel):
    """A proposed workflow/action to simulate.

    Represents a compiled DAG from Tier 3 ready for execution.
    """

    dag_id: str = Field(..., description="Unique DAG identifier")
    description: str = Field(..., description="What this DAG does")
    nodes: list[str] = Field(default_factory=list, description="Action node descriptions")
    has_external_calls: bool = Field(
        default=False,
        description="Whether the DAG makes external API/tool calls",
    )
    has_state_mutations: bool = Field(
        default=False,
        description="Whether the DAG modifies persistent state",
    )
    estimated_cost: float = Field(
        default=0.0,
        ge=0.0,
        description="Estimated resource cost",
    )
