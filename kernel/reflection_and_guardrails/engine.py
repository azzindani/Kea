"""
Tier 3 Reflection & Guardrails — Engine.

Pre-execution conscience and post-execution optimization:
    Pre:  1. Multi-path consensus evaluation (What-If)
          2. Value guardrails (ethics/security/corporate policy)
    Post: 3. Critique execution against hypotheses
          4. Generate optimization suggestions
          5. Commit lessons learned to long-term memory
"""

from __future__ import annotations

import time
from typing import Any

from shared.config import get_settings
from shared.id_and_hash import generate_id
from shared.logging.main import get_logger
from shared.standard_io import (
    Metrics,
    ModuleRef,
    Result,
    create_data_signal,
    fail,
    ok,
    processing_error,
    policy_error,
)

from kernel.scoring import score
from kernel.what_if_scenario import simulate_outcomes
from kernel.what_if_scenario.types import (
    CompiledDAG,
    SimulationVerdict,
    VerdictDecision,
)
from kernel.task_decomposition.types import WorldState
from kernel.graph_synthesizer.types import ExecutableDAG
from kernel.advanced_planning.types import ExpectedOutcome

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

log = get_logger(__name__)

_MODULE = "reflection_and_guardrails"
_TIER = 3


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


# ============================================================================
# Pre-Execution: Consensus Evaluation
# ============================================================================


async def evaluate_consensus(
    dag_candidates: list[ExecutableDAG],
) -> ExecutableDAG:
    """For critical tasks, score multiple DAG candidates via What-If.

    Takes a weighted vote based on plausibility scores to select
    the most likely success path. For non-critical tasks (single
    candidate), passes through directly.
    """
    settings = get_settings().kernel

    if len(dag_candidates) <= 1:
        return dag_candidates[0] if dag_candidates else ExecutableDAG(
            dag_id=generate_id("dag"),
            description="Empty DAG",
        )

    # Cap candidates to prevent runaway simulation
    candidates = dag_candidates[: settings.guardrail_max_consensus_candidates]

    best_dag = candidates[0]
    best_score = 0.0

    for dag in candidates:
        # Convert to CompiledDAG for What-If simulation
        compiled = CompiledDAG(
            dag_id=dag.dag_id,
            description=dag.description,
            nodes=[n.instruction.description for n in dag.nodes],
            has_external_calls=dag.has_external_calls,
            has_state_mutations=dag.has_state_mutations,
            estimated_cost=dag.estimated_cost,
        )

        knowledge = WorldState(goal=dag.description)
        result = await simulate_outcomes(compiled, knowledge)

        if result.signals:
            data = result.signals[0].body.get("data", {})
            if isinstance(data, dict):
                verdict = SimulationVerdict(**data)
                # Score: high reward + low risk = better candidate
                candidate_score = verdict.reward_score - (verdict.risk_score * 0.5)
                if candidate_score > best_score:
                    best_score = candidate_score
                    best_dag = dag

    log.info(
        "Consensus evaluation complete",
        candidates_evaluated=len(candidates),
        selected_dag=best_dag.dag_id,
        best_score=round(best_score, 3),
    )

    return best_dag


# ============================================================================
# Pre-Execution: Value Guardrails
# ============================================================================


def check_value_guardrails(dag: ExecutableDAG) -> GuardrailResult:
    """The final ethical/security/corporate gate before execution.

    Matches every node against Kea's non-negotiable rules:
    no data exfiltration, no unauthorized access, no privacy violations.
    """
    settings = get_settings().kernel
    violations: list[GuardrailViolation] = []
    forbidden_actions = settings.guardrail_forbidden_actions

    for node in dag.nodes:
        desc_lower = node.instruction.description.lower()

        for forbidden in forbidden_actions:
            # Check if any forbidden action pattern appears in the node
            forbidden_parts = forbidden.lower().split("_")
            if all(part in desc_lower for part in forbidden_parts):
                violations.append(GuardrailViolation(
                    rule_id=f"FORBIDDEN_{forbidden.upper()}",
                    node_id=node.node_id,
                    description=f"Node description matches forbidden action: {forbidden}",
                    severity="critical",
                ))

        # Check for tool calls that could be dangerous
        if node.instruction.action_type == "tool_call":
            tools = node.instruction.required_tools
            for tool in tools:
                tool_lower = tool.lower()
                if any(kw in tool_lower for kw in ("delete", "drop", "truncate", "destroy")):
                    violations.append(GuardrailViolation(
                        rule_id="DESTRUCTIVE_TOOL",
                        node_id=node.node_id,
                        description=f"Tool '{tool}' appears destructive",
                        severity="warning",
                    ))

    passed = not any(v.severity == "critical" for v in violations)

    result = GuardrailResult(
        passed=passed,
        violations=violations,
        policies_checked=len(forbidden_actions) * len(dag.nodes),
    )

    log.info(
        "Guardrail check complete",
        dag_id=dag.dag_id,
        passed=passed,
        violations=len(violations),
        policies_checked=result.policies_checked,
    )

    return result


# ============================================================================
# Pre-Execution: Top-Level Check
# ============================================================================


async def run_pre_execution_check(dag: ExecutableDAG) -> Result:
    """Top-level pre-execution orchestrator (The Conscience).

    Runs consensus evaluation (if multiple candidates) and value
    guardrails before allowing execution.
    """
    ref = _ref("run_pre_execution_check")
    start = time.perf_counter()

    try:
        # Check guardrails
        guardrail_result = check_value_guardrails(dag)

        if not guardrail_result.passed:
            # Critical violations → reject
            critical_violations = [
                v for v in guardrail_result.violations if v.severity == "critical"
            ]
            decision = ApprovalDecision.REJECTED
            reasoning = (
                f"DAG rejected due to {len(critical_violations)} critical "
                f"guardrail violations: "
                + "; ".join(v.description for v in critical_violations)
            )
            safeguards: list[str] = []

        elif guardrail_result.violations:
            # Non-critical violations → modify with safeguards
            decision = ApprovalDecision.MODIFIED
            reasoning = (
                f"DAG approved with {len(guardrail_result.violations)} "
                f"warnings requiring safeguards"
            )
            safeguards = [
                f"Add safety gate before node {v.node_id}: {v.description}"
                for v in guardrail_result.violations
            ]

        else:
            decision = ApprovalDecision.APPROVED
            reasoning = "All guardrail checks passed"
            safeguards = []

        approval = ApprovalResult(
            decision=decision,
            reasoning=reasoning,
            guardrail_result=guardrail_result,
            safeguard_nodes=safeguards,
        )

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)

        signal = create_data_signal(
            data=approval.model_dump(),
            schema="ApprovalResult",
            origin=ref,
            trace_id="",
            tags={
                "decision": decision.value,
                "violations": str(len(guardrail_result.violations)),
            },
        )

        log.info(
            "Pre-execution check complete",
            decision=decision.value,
            violations=len(guardrail_result.violations),
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Pre-execution check failed: {exc}",
            source=ref,
            detail={"dag_id": dag.dag_id, "error_type": type(exc).__name__},
        )
        log.error("Pre-execution check failed", error=str(exc))
        return fail(error=error, metrics=metrics)


# ============================================================================
# Post-Execution: Critique
# ============================================================================


def critique_execution(
    result: ExecutionResult,
    expected: list[ExpectedOutcome],
) -> CritiqueReport:
    """Compare actual outcomes against pre-execution hypotheses.

    Identifies what went right, what went wrong, and root causes.
    """
    evaluations: list[HypothesisEvaluation] = []
    strengths: list[str] = []
    root_causes: list[str] = []

    for hypothesis in expected:
        task_id = hypothesis.task_id
        actual = result.outputs.get(task_id)

        # Check if the task completed
        if task_id in result.completed_nodes:
            # Evaluate against success criteria
            met = True
            for key, expected_val in hypothesis.success_criteria.items():
                if key == "success":
                    # Was the task successful overall?
                    met = met and (task_id not in result.failed_nodes)
                elif expected_val == "not_null":
                    met = met and (actual is not None)
                else:
                    actual_val = actual.get(key) if isinstance(actual, dict) else None
                    met = met and (actual_val == expected_val)

            gap = 0.0 if met else 0.5
            if met:
                strengths.append(
                    f"Task '{task_id}' met expectations: {hypothesis.description}"
                )
        else:
            met = False
            gap = 1.0
            if task_id in result.failed_nodes:
                root_causes.append(
                    f"Task '{task_id}' failed: check error logs for details"
                )
            else:
                root_causes.append(
                    f"Task '{task_id}' did not complete"
                )

        evaluations.append(HypothesisEvaluation(
            task_id=task_id,
            hypothesis_description=hypothesis.description,
            met=met,
            actual_value=actual,
            expected_criteria=hypothesis.success_criteria,
            gap_score=gap,
        ))

    met_count = sum(1 for e in evaluations if e.met)
    success_rate = met_count / len(evaluations) if evaluations else 0.0

    report = CritiqueReport(
        dag_id=result.dag_id,
        hypothesis_evaluations=evaluations,
        success_rate=round(success_rate, 3),
        root_causes=root_causes,
        strengths=strengths,
    )

    log.info(
        "Execution critique complete",
        dag_id=result.dag_id,
        success_rate=round(success_rate, 3),
        hypotheses_met=met_count,
        hypotheses_total=len(evaluations),
    )

    return report


# ============================================================================
# Post-Execution: Optimize
# ============================================================================


def optimize_loop(critique: CritiqueReport) -> list[OptimizationSuggestion]:
    """Generate actionable optimization suggestions from critique.

    If a node consistently fails, suggests alternative tool bindings.
    If a sequence is slow, suggests parallelization.
    """
    settings = get_settings().kernel
    suggestions: list[OptimizationSuggestion] = []

    for evaluation in critique.hypothesis_evaluations:
        if evaluation.met:
            continue

        gap = evaluation.gap_score

        # Complete failure → suggest retry or tool rebind
        if gap >= settings.reflection_min_score_gap:
            suggestions.append(OptimizationSuggestion(
                suggestion_id=generate_id("opt"),
                optimization_type=OptimizationType.ADD_RETRY,
                description=f"Add retry logic for task '{evaluation.task_id}' (gap: {gap:.2f})",
                target_node_ids=[evaluation.task_id],
                confidence=0.6,
                estimated_improvement=0.3,
            ))

        # Large gap → suggest tool rebind
        if gap >= 0.7:
            suggestions.append(OptimizationSuggestion(
                suggestion_id=generate_id("opt"),
                optimization_type=OptimizationType.TOOL_REBIND,
                description=f"Consider alternative tool for task '{evaluation.task_id}'",
                target_node_ids=[evaluation.task_id],
                confidence=0.4,
                estimated_improvement=0.4,
            ))

    # If overall success rate is low, suggest simplification
    if critique.success_rate < 0.5 and len(critique.hypothesis_evaluations) > 2:
        suggestions.append(OptimizationSuggestion(
            suggestion_id=generate_id("opt"),
            optimization_type=OptimizationType.SIMPLIFY,
            description="Overall success rate is low; consider simplifying the DAG",
            confidence=0.5,
            estimated_improvement=0.3,
        ))

    log.info("Optimization suggestions generated", count=len(suggestions))
    return suggestions


# ============================================================================
# Post-Execution: Commit Policy Update
# ============================================================================


async def commit_policy_update(
    suggestions: list[OptimizationSuggestion],
    critique: CritiqueReport,
) -> ReflectionInsight:
    """Package optimization suggestions into a ReflectionInsight.

    In production, this would commit to Tier 5 / Vault via API.
    Currently packages the insight for upstream consumption.
    """
    insight = ReflectionInsight(
        insight_id=generate_id("insight"),
        dag_id=critique.dag_id,
        critique_summary=(
            f"Success rate: {critique.success_rate:.1%}. "
            f"Strengths: {len(critique.strengths)}. "
            f"Root causes: {len(critique.root_causes)}."
        ),
        suggestions=suggestions,
        success_rate=critique.success_rate,
        committed_to_vault=False,  # Vault integration is via service API
    )

    log.info(
        "Reflection insight packaged",
        insight_id=insight.insight_id,
        dag_id=critique.dag_id,
        suggestions=len(suggestions),
    )

    return insight


# ============================================================================
# Post-Execution: Top-Level Reflection
# ============================================================================


async def run_post_execution_reflection(
    result: ExecutionResult,
    expected: list[ExpectedOutcome],
) -> Result:
    """Top-level post-execution orchestrator (Continuous Optimization).

    Critiques execution, generates optimization suggestions,
    and packages lessons learned for Tier 5 persistence.
    """
    ref = _ref("run_post_execution_reflection")
    start = time.perf_counter()

    try:
        # Step 1: Critique
        critique = critique_execution(result, expected)

        # Step 2: Optimize
        suggestions = optimize_loop(critique)

        # Step 3: Commit
        insight = await commit_policy_update(suggestions, critique)

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)

        signal = create_data_signal(
            data=insight.model_dump(),
            schema="ReflectionInsight",
            origin=ref,
            trace_id="",
            tags={
                "dag_id": result.dag_id,
                "success_rate": f"{critique.success_rate:.3f}",
                "suggestions": str(len(suggestions)),
            },
        )

        log.info(
            "Post-execution reflection complete",
            dag_id=result.dag_id,
            success_rate=round(critique.success_rate, 3),
            suggestions=len(suggestions),
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Post-execution reflection failed: {exc}",
            source=ref,
            detail={"dag_id": result.dag_id, "error_type": type(exc).__name__},
        )
        log.error("Post-execution reflection failed", error=str(exc))
        return fail(error=error, metrics=metrics)
