"""
Tier 3: Reflection & Guardrails Module.

Pre-execution conscience gates and post-execution reflection
for continuous improvement.

Usage::

    from kernel.reflection_and_guardrails import (
        run_pre_execution_check,
        run_post_execution_reflection,
    )

    # Pre-execution
    approval = await run_pre_execution_check(dag)

    # Post-execution
    insight = await run_post_execution_reflection(result, expected)
"""

from .engine import (
    check_value_guardrails,
    commit_policy_update,
    critique_execution,
    evaluate_consensus,
    optimize_loop,
    run_post_execution_reflection,
    run_pre_execution_check,
)
from .types import (
    ApprovalDecision,
    ApprovalResult,
    CritiqueReport,
    ExecutionResult,
    GuardrailResult,
    GuardrailViolation,
    HypothesisEvaluation,
    OptimizationSuggestion,
    OptimizationType,
    ReflectionInsight,
)

__all__ = [
    "run_pre_execution_check",
    "evaluate_consensus",
    "check_value_guardrails",
    "run_post_execution_reflection",
    "critique_execution",
    "optimize_loop",
    "commit_policy_update",
    "ApprovalDecision",
    "ApprovalResult",
    "CritiqueReport",
    "ExecutionResult",
    "GuardrailResult",
    "GuardrailViolation",
    "HypothesisEvaluation",
    "OptimizationSuggestion",
    "OptimizationType",
    "ReflectionInsight",
]
