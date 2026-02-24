"""
Tier 3 Reflection & Guardrails — Types.

Pydantic models for pre-execution conscience gates, post-execution
reflection/critique, and continuous optimization.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ============================================================================
# Pre-Execution: Approval
# ============================================================================


class ApprovalDecision(str, Enum):
    """Pre-execution gate decision."""

    APPROVED = "approved"   # Safe to execute
    REJECTED = "rejected"   # Abort with reason
    MODIFIED = "modified"   # Execute with appended safeguard nodes


class GuardrailViolation(BaseModel):
    """A specific policy violation detected by the guardrails."""

    rule_id: str = Field(..., description="Which rule was violated")
    node_id: str = Field(..., description="Which DAG node triggered the violation")
    description: str = Field(..., description="Human-readable violation detail")
    severity: str = Field(
        default="warning",
        description="Violation severity (info, warning, critical)",
    )


class GuardrailResult(BaseModel):
    """Result of the value guardrail check."""

    passed: bool = Field(..., description="Whether all guardrails passed")
    violations: list[GuardrailViolation] = Field(default_factory=list)
    policies_checked: int = Field(default=0, ge=0)


class ApprovalResult(BaseModel):
    """Combined pre-execution check result."""

    decision: ApprovalDecision = Field(...)
    reasoning: str = Field(..., description="Why this decision was made")
    guardrail_result: GuardrailResult = Field(default_factory=GuardrailResult)
    safeguard_nodes: list[str] = Field(
        default_factory=list,
        description="Node descriptions to append (for MODIFIED decision)",
    )


# ============================================================================
# Post-Execution: Reflection
# ============================================================================


class ExecutionResult(BaseModel):
    """The actual outcome from Tier 4 execution — input to reflection."""

    dag_id: str = Field(..., description="Which DAG was executed")
    completed_nodes: list[str] = Field(default_factory=list)
    failed_nodes: list[str] = Field(default_factory=list)
    outputs: dict[str, Any] = Field(
        default_factory=dict,
        description="Actual output values keyed by node ID",
    )
    total_duration_ms: float = Field(default=0.0, ge=0.0)
    total_cost: float = Field(default=0.0, ge=0.0)
    errors: list[str] = Field(
        default_factory=list,
        description="Error messages from failed nodes",
    )


class HypothesisEvaluation(BaseModel):
    """Comparison of a single hypothesis against actual outcome."""

    task_id: str = Field(...)
    hypothesis_description: str = Field(...)
    met: bool = Field(..., description="Whether the expectation was met")
    actual_value: Any = Field(default=None, description="What was actually produced")
    expected_criteria: dict[str, Any] = Field(default_factory=dict)
    gap_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Quantified gap between expected and actual",
    )


class CritiqueReport(BaseModel):
    """Post-execution critique: what went right and wrong."""

    dag_id: str = Field(...)
    hypothesis_evaluations: list[HypothesisEvaluation] = Field(default_factory=list)
    success_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Fraction of hypotheses met",
    )
    root_causes: list[str] = Field(
        default_factory=list,
        description="Identified root causes for failures",
    )
    strengths: list[str] = Field(
        default_factory=list,
        description="What worked well",
    )


# ============================================================================
# Optimization & Policy Updates
# ============================================================================


class OptimizationType(str, Enum):
    """Category of optimization suggestion."""

    TOOL_REBIND = "tool_rebind"             # Try a different MCP tool
    PARALLELIZE = "parallelize"              # Convert sequential to parallel
    ADJUST_HYPOTHESIS = "adjust_hypothesis"  # Recalibrate expectations
    ADD_RETRY = "add_retry"                  # Add retry logic for flaky nodes
    SIMPLIFY = "simplify"                    # Remove unnecessary nodes
    REORDER = "reorder"                      # Change execution sequence


class OptimizationSuggestion(BaseModel):
    """An actionable suggestion for improving future DAG cycles."""

    suggestion_id: str = Field(...)
    optimization_type: OptimizationType = Field(...)
    description: str = Field(..., description="What should change")
    target_node_ids: list[str] = Field(
        default_factory=list,
        description="Which nodes this applies to",
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence that this suggestion will improve outcomes",
    )
    estimated_improvement: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Expected improvement in success rate",
    )


class ReflectionInsight(BaseModel):
    """A packaged lesson learned, ready for Vault persistence.

    Committed to Tier 5 long-term memory for cross-epoch improvement.
    """

    insight_id: str = Field(...)
    dag_id: str = Field(...)
    critique_summary: str = Field(..., description="Key takeaways from the critique")
    suggestions: list[OptimizationSuggestion] = Field(default_factory=list)
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    committed_to_vault: bool = Field(
        default=False,
        description="Whether this insight has been persisted",
    )
