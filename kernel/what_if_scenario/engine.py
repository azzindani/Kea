"""
Tier 2 What-If Scenario — Engine.

Offline counter-factual simulation pipeline:
    1. Generate outcome branches (success/failure trees)
    2. Predict environmental consequences
    3. Calculate risk/reward ratio → SimulationVerdict
"""

from __future__ import annotations

import json
import time

from kernel.intent_sentiment_urgency import score_urgency
from kernel.task_decomposition.types import WorldState
from shared.config import get_settings
from shared.id_and_hash import generate_id
from shared.inference_kit import InferenceKit
from shared.llm.provider import LLMMessage
from shared.logging.main import get_logger
from shared.normalization import min_max_scale
from shared.standard_io import (
    Metrics,
    ModuleRef,
    Result,
    create_data_signal,
    fail,
    ok,
    processing_error,
)

from .types import (
    CompiledDAG,
    ConsequencePrediction,
    OutcomeBranch,
    SimulationVerdict,
    VerdictDecision,
)

log = get_logger(__name__)

_MODULE = "what_if_scenario"
_TIER = 2


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


# ============================================================================
# Step 1: Generate Outcome Branches
# ============================================================================


def generate_outcome_branches(
    action: CompiledDAG,
    knowledge: WorldState,
) -> list[OutcomeBranch]:
    """Generate a tree of possible outcomes for the proposed action.

    At minimum produces a success branch and a failure branch.
    For complex DAGs, generates branches at each decision point.
    """
    settings = get_settings().kernel
    branches: list[OutcomeBranch] = []

    # Always generate success branch
    branches.append(OutcomeBranch(
        branch_id=generate_id("node"),
        description=f"Successful execution of: {action.description}",
        is_success=True,
        likelihood=0.7 if not action.has_external_calls else 0.5,
        terminal_state="All nodes executed successfully",
        path_steps=[f"Execute {n}" for n in action.nodes],
    ))

    # Always generate primary failure branch
    failure_likelihood = 0.3 if not action.has_external_calls else 0.5
    branches.append(OutcomeBranch(
        branch_id=generate_id("node"),
        description=f"Failure during: {action.description}",
        is_success=False,
        likelihood=failure_likelihood,
        terminal_state="Execution halted due to error",
        path_steps=[f"Execute {action.nodes[0]}" if action.nodes else "Start", "Error encountered"],
    ))

    # Additional branches for complex DAGs
    if len(action.nodes) > 2 and len(branches) < settings.max_simulation_branches:
        # Partial success branch
        mid_point = len(action.nodes) // 2
        branches.append(OutcomeBranch(
            branch_id=generate_id("node"),
            description=f"Partial execution: {mid_point}/{len(action.nodes)} nodes complete",
            is_success=False,
            likelihood=0.15,
            terminal_state=f"Stalled at node {mid_point + 1}",
            path_steps=[f"Execute {n}" for n in action.nodes[:mid_point]] + ["Stall"],
        ))

    if action.has_external_calls and len(branches) < settings.max_simulation_branches:
        # External service timeout branch
        branches.append(OutcomeBranch(
            branch_id=generate_id("node"),
            description="External service timeout or unavailability",
            is_success=False,
            likelihood=0.1,
            terminal_state="External dependency unreachable",
            path_steps=["Initiate external call", "Timeout after retry"],
        ))

    return branches


# ============================================================================
# Step 2: Predict Consequences
# ============================================================================


async def predict_consequences(
    branches: list[OutcomeBranch],
    kit: InferenceKit | None = None,
) -> list[ConsequencePrediction]:
    """Predict environmental side effects for each outcome branch.

    Uses T1 urgency scoring to weight severity of negative consequences.
    """
    predictions: list[ConsequencePrediction] = []

    for branch in branches:
        # Use urgency scoring on the branch description for severity
        urgency = score_urgency(branch.description)
        severity = urgency.score if not branch.is_success else 0.0

        # Determine resource impact
        resource_impact = "low"
        if len(branch.path_steps) > 5:
            resource_impact = "high"
        elif len(branch.path_steps) > 2:
            resource_impact = "medium"

        # LLM based enrichment
        state_mutations = [f"State change from: {step}" for step in branch.path_steps if "Execute" in step]
        external_impacts = (
            ["External service affected"]
            if any("external" in step.lower() for step in branch.path_steps)
            else []
        )

        if kit and kit.has_llm:
            try:
                system_msg = LLMMessage(
                    role="system",
                    content="Analyze the consequence branch and predict side effects. Respond EXACTLY with JSON: {\"resource_impact\": \"high|medium|low\", \"state_mutations\": [\"...\"], \"external_impacts\": [\"...\"]}"
                )
                user_msg = LLMMessage(role="user", content=f"Branch: {branch.description}\nSteps: {branch.path_steps}")
                resp = await kit.llm.complete([system_msg, user_msg], kit.llm_config)

                content = resp.content.strip()
                if content.startswith("```json"):
                    content = content[7:-3].strip()
                elif content.startswith("```"):
                    content = content[3:-3].strip()
                data = json.loads(content)

                resource_impact = data.get("resource_impact", resource_impact)
                if data.get("state_mutations"):
                    state_mutations.extend(data["state_mutations"])
                if data.get("external_impacts"):
                    external_impacts.extend(data["external_impacts"])
            except Exception as e:
                log.warning("LLM consequence prediction failed", error=str(e))
                pass

        predictions.append(ConsequencePrediction(
            branch_id=branch.branch_id,
            resource_impact=resource_impact,
            state_mutations=state_mutations,
            reversible=branch.is_success,
            severity_score=severity,
            external_impacts=external_impacts,
        ))

    return predictions


# ============================================================================
# Step 3: Calculate Risk/Reward
# ============================================================================


def calculate_risk_reward(
    predictions: list[ConsequencePrediction],
) -> SimulationVerdict:
    """Aggregate predictions into risk/reward ratio and produce verdict.

    Compares against config-driven thresholds for the final decision.
    """
    settings = get_settings().kernel

    if not predictions:
        return SimulationVerdict(
            decision=VerdictDecision.APPROVE,
            risk_score=0.0,
            reward_score=1.0,
            reasoning="No predictions to evaluate; defaulting to approve",
            branches_analyzed=0,
        )

    # Aggregate risk
    total_severity = sum(p.severity_score for p in predictions)
    avg_severity = total_severity / len(predictions)

    # Weight by irreversibility
    irreversible_count = sum(1 for p in predictions if not p.reversible)
    irreversible_penalty = irreversible_count / len(predictions) * 0.3

    risk_score = min_max_scale(
        avg_severity + irreversible_penalty, 0.0, 2.0,
    )

    # Reward: inverse of risk, weighted by success branch likelihood
    reward_score = max(0.0, 1.0 - risk_score)

    # Decision based on thresholds
    safeguards: list[str] = []

    if risk_score <= settings.risk_threshold_approve:
        decision = VerdictDecision.APPROVE
        reasoning = (
            f"Risk score {risk_score:.3f} is below approval threshold "
            f"{settings.risk_threshold_approve}. Proceeding safely."
        )

    elif risk_score >= settings.risk_threshold_reject:
        decision = VerdictDecision.REJECT
        reasoning = (
            f"Risk score {risk_score:.3f} exceeds rejection threshold "
            f"{settings.risk_threshold_reject}. Alternative approach required."
        )

    else:
        decision = VerdictDecision.MODIFY
        reasoning = (
            f"Risk score {risk_score:.3f} is moderate (between "
            f"{settings.risk_threshold_approve} and {settings.risk_threshold_reject}). "
            f"Appending safeguards before execution."
        )
        # Generate safeguard recommendations
        for pred in predictions:
            if not pred.reversible:
                safeguards.append(f"Add rollback mechanism for: {pred.branch_id}")
            if pred.external_impacts:
                safeguards.append("Add circuit breaker for external calls")
            if pred.resource_impact == "high":
                safeguards.append("Add resource budget check before execution")

    return SimulationVerdict(
        decision=decision,
        risk_score=risk_score,
        reward_score=reward_score,
        reasoning=reasoning,
        safeguards=safeguards,
        branches_analyzed=len(predictions),
    )


# ============================================================================
# Top-Level Orchestrator
# ============================================================================


async def simulate_outcomes(
    proposed_action: CompiledDAG,
    knowledge: WorldState,
    kit: InferenceKit | None = None,
) -> Result:
    """Top-level simulation orchestrator.

    Generates outcome branches, predicts consequences, calculates
    risk/reward, and returns a SimulationVerdict.
    """
    ref = _ref("simulate_outcomes")
    start = time.perf_counter()

    try:
        # Step 1: Generate branches
        branches = generate_outcome_branches(proposed_action, knowledge)

        # Step 2: Predict consequences
        predictions = await predict_consequences(branches, kit)

        # Step 3: Calculate risk/reward
        verdict = calculate_risk_reward(predictions)

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)

        signal = create_data_signal(
            data=verdict.model_dump(),
            schema="SimulationVerdict",
            origin=ref,
            trace_id="",
            tags={
                "decision": verdict.decision.value,
                "risk": f"{verdict.risk_score:.3f}",
            },
        )

        log.info(
            "Simulation complete",
            decision=verdict.decision.value,
            risk=round(verdict.risk_score, 3),
            reward=round(verdict.reward_score, 3),
            branches=len(branches),
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Simulation failed: {exc}",
            source=ref,
            detail={"dag_id": proposed_action.dag_id, "error_type": type(exc).__name__},
        )
        log.error("Simulation failed", error=str(exc))
        return fail(error=error, metrics=metrics)
