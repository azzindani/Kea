"""
Tier 6 Self Model — Engine.

The agent's internal representation of itself:
    1. Assess capability against an incoming signal
    2. Track current cognitive state (introspection)
    3. Update accuracy history for calibration feedback
    4. Detect capability gaps (missing tools, knowledge, constraints)
    5. Refresh capability map from external sources
"""

from __future__ import annotations

import json
import time
from typing import Any

from kernel.lifecycle_controller.types import IdentityContext
from shared.config import get_settings
from shared.inference_kit import InferenceKit
from shared.llm.provider import LLMMessage
from shared.logging.main import get_logger
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
    AgentCognitiveState,
    CalibrationDataPoint,
    CalibrationHistory,
    CapabilityAssessment,
    CapabilityGap,
    ProcessingPhase,
    SignalTags,
)

log = get_logger(__name__)

_MODULE = "self_model"
_TIER = 6


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


# ============================================================================
# Internal State (module-level, refreshed at genesis and periodically)
# ============================================================================

_known_skills: set[str] = set()
_available_tools: set[str] = set()
_knowledge_domains: set[str] = set()
_constraint_boundaries: list[str] = []
_calibration_history: CalibrationHistory = CalibrationHistory()
_cognitive_state: AgentCognitiveState = AgentCognitiveState()


# ============================================================================
# Step 1: Assess Capability
# ============================================================================


async def assess_capability(
    signal_tags: SignalTags,
    identity: IdentityContext,
    kit: InferenceKit | None = None,
) -> CapabilityAssessment:
    """Top-level capability check.

    Cross-references the incoming signal's domain, required skills,
    and tool needs against the agent's Capability Map. Returns a
    verdict on whether the agent can handle this signal.
    """
    gap = await detect_capability_gap(signal_tags, identity, kit)

    # If no gap, fully capable
    if gap is None:
        return CapabilityAssessment(
            can_handle=True,
            confidence=0.95,
            gap=None,
            partial_capabilities=list(identity.skills),
        )

    # Calculate severity based on gap composition
    severity = gap.severity

    # Determine partial capabilities — skills the agent HAS
    matched_skills = [
        s for s in signal_tags.required_skills if s in identity.skills
    ]

    can_handle = severity < 0.5

    log.debug(
        "Capability assessed",
        can_handle=can_handle,
        severity=round(severity, 3),
        missing_tools=len(gap.missing_tools),
        missing_knowledge=len(gap.missing_knowledge),
    )

    return CapabilityAssessment(
        can_handle=can_handle,
        confidence=max(0.0, 1.0 - severity),
        gap=gap,
        partial_capabilities=matched_skills,
    )


# ============================================================================
# Step 2: Get Current State
# ============================================================================


def get_current_state() -> AgentCognitiveState:
    """Return a snapshot of the agent's current cognitive state.

    Reports which modules are active, what processing phase we're in,
    OODA cycle count, current task context, and elapsed time.
    """
    return _cognitive_state.model_copy()


def update_cognitive_state(
    *,
    agent_id: str | None = None,
    processing_phase: ProcessingPhase | None = None,
    active_modules: list[str] | None = None,
    current_task_description: str | None = None,
    ooda_cycle_count: int | None = None,
    elapsed_ms: float | None = None,
    current_dag_id: str | None = None,
) -> AgentCognitiveState:
    """Update the agent's cognitive state (called by T4/T5)."""
    global _cognitive_state

    updates: dict[str, Any] = {}
    if agent_id is not None:
        updates["agent_id"] = agent_id
    if processing_phase is not None:
        updates["processing_phase"] = processing_phase
    if active_modules is not None:
        updates["active_modules"] = active_modules
    if current_task_description is not None:
        updates["current_task_description"] = current_task_description
    if ooda_cycle_count is not None:
        updates["ooda_cycle_count"] = ooda_cycle_count
    if elapsed_ms is not None:
        updates["elapsed_ms"] = elapsed_ms
    if current_dag_id is not None:
        updates["current_dag_id"] = current_dag_id

    _cognitive_state = _cognitive_state.model_copy(update=updates)
    return _cognitive_state


# ============================================================================
# Step 3: Update Accuracy History
# ============================================================================


def update_accuracy_history(
    predicted: float,
    actual: float,
    domain: str = "general",
) -> None:
    """Record a calibration data point.

    When the agent predicts a confidence level and the actual outcome
    is later known, this updates the running calibration curve.
    """
    global _calibration_history
    settings = get_settings().kernel

    point = CalibrationDataPoint(
        predicted=max(0.0, min(1.0, predicted)),
        actual=max(0.0, min(1.0, actual)),
        domain=domain,
    )
    _calibration_history.data_points.append(point)

    # Apply EMA to domain accuracy
    decay = settings.self_model_calibration_ema_decay
    current_domain_acc = _calibration_history.domain_accuracy.get(domain, 0.5)
    updated_acc = (1 - decay) * current_domain_acc + decay * actual
    _calibration_history.domain_accuracy[domain] = round(updated_acc, 6)

    # Update overall accuracy
    if _calibration_history.domain_accuracy:
        _calibration_history.overall_accuracy = round(
            sum(_calibration_history.domain_accuracy.values())
            / len(_calibration_history.domain_accuracy),
            6,
        )

    _calibration_history.sample_count += 1

    # Trim to window size
    window = settings.self_model_calibration_window
    if len(_calibration_history.data_points) > window:
        _calibration_history.data_points = _calibration_history.data_points[-window:]

    log.debug(
        "Accuracy history updated",
        domain=domain,
        predicted=round(predicted, 3),
        actual=round(actual, 3),
        sample_count=_calibration_history.sample_count,
    )


def get_calibration_history() -> CalibrationHistory:
    """Return the current calibration history."""
    return _calibration_history.model_copy(deep=True)


# ============================================================================
# Step 4: Detect Capability Gap
# ============================================================================


async def detect_capability_gap(
    signal_tags: SignalTags,
    identity: IdentityContext | None = None,
    kit: InferenceKit | None = None,
) -> CapabilityGap | None:
    """Compare signal requirements against the agent's Capability Map.

    Returns None if fully capable, or a CapabilityGap detailing
    what's missing: tools, knowledge domains, or constraint violations.
    """
    missing_tools: list[str] = []
    missing_knowledge: list[str] = []
    constraint_violations: list[str] = []

    # Check required tools
    available = _available_tools
    if identity is not None:
        available = available | set(identity.tools_allowed)

    for tool in signal_tags.required_tools:
        if tool not in available:
            missing_tools.append(tool)
        if identity is not None and tool in identity.tools_forbidden:
            constraint_violations.append(f"tool_forbidden:{tool}")

    # Check required skills
    agent_skills = _known_skills
    if identity is not None:
        agent_skills = agent_skills | set(identity.skills)

    for skill in signal_tags.required_skills:
        if skill not in agent_skills:
            missing_knowledge.append(skill)

    if kit and kit.has_llm and missing_knowledge and agent_skills:
        try:
            system_msg = LLMMessage(
                role="system",
                content="Given the agent's known skills, are the missing skills actually covered by implication? Return a JSON list of strictly missing skills."
            )
            user_msg = LLMMessage(role="user", content=f"Known: {list(agent_skills)}\nMissing: {missing_knowledge}")
            resp = await kit.llm.complete([system_msg, user_msg], kit.llm_config)

            content = resp.content.strip()
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            data = json.loads(content)

            if isinstance(data, list):
                missing_knowledge = [str(s) for s in data]
        except Exception as e:
            log.warning("LLM capability gap check failed", error=str(e))
            pass

    # Check domain coverage
    domains = _knowledge_domains
    if identity is not None:
        domains = domains | set(identity.knowledge_domains)

    if signal_tags.domain != "general" and signal_tags.domain not in domains:
        # If the agent has the 'general' domain, it is considered capable of handling 
        # specific domains without a hard gap (though with potentially lower performance).
        if "general" not in domains:
            missing_knowledge.append(f"domain:{signal_tags.domain}")

    # No gaps found
    if not missing_tools and not missing_knowledge and not constraint_violations:
        return None

    # Calculate severity: weighted by category
    total_requirements = max(
        1,
        len(signal_tags.required_tools)
        + len(signal_tags.required_skills)
        + (1 if signal_tags.domain != "general" else 0),
    )
    total_missing = len(missing_tools) + len(missing_knowledge)
    constraint_penalty = len(constraint_violations) * 0.3

    severity = min(1.0, (total_missing / total_requirements) + constraint_penalty)

    return CapabilityGap(
        missing_tools=missing_tools,
        missing_knowledge=missing_knowledge,
        constraint_violations=constraint_violations,
        severity=round(severity, 3),
    )


# ============================================================================
# Step 5: Refresh Capability Map
# ============================================================================


async def refresh_capability_map(
    identity: IdentityContext | None = None,
    available_tools: list[str] | None = None,
    knowledge_domains: list[str] | None = None,
) -> None:
    """Rebuild the Capability Map from current sources.

    Called at agent genesis, after tool discovery events, and
    periodically during long-running tasks. In the kernel layer,
    the actual MCP Host and RAG Service queries are delegated to
    the service layer — here we accept the resolved lists.
    """
    global _known_skills, _available_tools, _knowledge_domains, _constraint_boundaries

    if identity is not None:
        _known_skills = set(identity.skills)
        _constraint_boundaries = list(identity.ethical_constraints)

    if available_tools is not None:
        _available_tools = set(available_tools)

    if knowledge_domains is not None:
        _knowledge_domains = set(knowledge_domains)

    log.info(
        "Capability map refreshed",
        skills=len(_known_skills),
        tools=len(_available_tools),
        domains=len(_knowledge_domains),
        constraints=len(_constraint_boundaries),
    )


# ============================================================================
# Top-Level Orchestrator
# ============================================================================


async def run_self_model(
    signal_tags: SignalTags,
    identity: IdentityContext,
    kit: InferenceKit | None = None,
) -> Result:
    """Top-level Self-Model evaluation.

    Assesses capability, captures cognitive state, and packages
    the results into a standard Result for the pipeline.
    """
    ref = _ref("run_self_model")
    start = time.perf_counter()

    try:
        # Assess capability for this signal
        assessment = await assess_capability(signal_tags, identity, kit)

        # Capture current cognitive state
        state = get_current_state()

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)

        signal = create_data_signal(
            data={
                "assessment": assessment.model_dump(),
                "cognitive_state": state.model_dump(),
            },
            schema="SelfModelOutput",
            origin=ref,
            trace_id="",
            tags={
                "can_handle": str(assessment.can_handle),
                "confidence": f"{assessment.confidence:.3f}",
                "phase": state.processing_phase.value,
            },
        )

        log.info(
            "Self-model evaluation complete",
            can_handle=assessment.can_handle,
            confidence=round(assessment.confidence, 3),
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Self-model evaluation failed: {exc}",
            source=ref,
            detail={"error_type": type(exc).__name__},
        )
        log.error("Self-model evaluation failed", error=str(exc))
        return fail(error=error, metrics=metrics)
