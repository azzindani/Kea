"""
Tier 5 Lifecycle Controller — Engine.

Agent lifecycle management:
    1. Initialize agent (genesis + identity registration)
    2. Load cognitive profile from Vault
    3. Set immutable identity constraints
    4. Track macro-objectives across OODA epochs
    5. Control sleep/wake/panic lifecycle transitions
    6. Commit epoch memory to Vault for persistence
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
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
)

from kernel.short_term_memory import ShortTermMemory
from kernel.short_term_memory.types import EpochSummary
from kernel.ooda_loop.types import MacroObjective

from .types import (
    AgentIdentity,
    AgentLifecycle,
    CognitiveProfile,
    IdentityContext,
    LifecyclePhase,
    LifecycleSignal,
    LifecycleSignalType,
    LifecycleState,
    ObjectiveState,
    ObjectiveStatus,
    SpawnRequest,
)

log = get_logger(__name__)

_MODULE = "lifecycle_controller"
_TIER = 5


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


# ============================================================================
# Step 1: Agent Genesis
# ============================================================================


async def initialize_agent(spawn_request: SpawnRequest) -> AgentIdentity:
    """Create a new agent instance.

    Generates unique ID, registers identity, and initializes
    internal state structures.
    """
    agent_id = generate_id("agent")

    identity = AgentIdentity(
        agent_id=agent_id,
        role=spawn_request.role,
        profile_id=spawn_request.profile_id,
        created_utc=_now_utc(),
    )

    log.info(
        "Agent initialized",
        agent_id=agent_id,
        role=spawn_request.role,
        profile_id=spawn_request.profile_id,
    )

    return identity


# ============================================================================
# Step 2: Load Cognitive Profile
# ============================================================================


async def load_cognitive_profile(profile_id: str) -> CognitiveProfile:
    """Retrieve the agent's cognitive profile.

    In production, this calls the Vault Service HTTP API.
    Here we construct a default profile from config for the kernel layer.
    """
    settings = get_settings().kernel

    # The actual profile loading is delegated to the Vault service.
    # The kernel provides the interface contract; the service layer
    # performs the HTTP call. Here we return a default profile that
    # the service layer will override.
    profile = CognitiveProfile(
        profile_id=profile_id or generate_id("profile"),
        role_name="default",
        skills=["general"],
        knowledge_domains=["general"],
        quality_bar=settings.noise_gate_grounding_threshold,
    )

    log.info(
        "Cognitive profile loaded",
        profile_id=profile.profile_id,
        role=profile.role_name,
    )

    return profile


# ============================================================================
# Step 3: Set Identity Constraints
# ============================================================================


def set_identity_constraints(
    agent_id: str,
    profile: CognitiveProfile,
) -> IdentityContext:
    """Convert cognitive profile into immutable identity context.

    Once set, this context cannot be modified by any lower-tier component.
    """
    context = IdentityContext(
        agent_id=agent_id,
        role=profile.role_name,
        skills=frozenset(profile.skills),
        tools_allowed=frozenset(profile.tools_allowed),
        tools_forbidden=frozenset(profile.tools_forbidden),
        knowledge_domains=frozenset(profile.knowledge_domains),
        ethical_constraints=tuple(profile.ethical_constraints),
        quality_bar=profile.quality_bar,
    )

    log.info(
        "Identity constraints set",
        agent_id=agent_id,
        role=profile.role_name,
        skills_count=len(profile.skills),
        constraints_count=len(profile.ethical_constraints),
    )

    return context


# ============================================================================
# Step 4: Track Macro-Objectives
# ============================================================================


def track_macro_objective(
    objective: MacroObjective,
    stm: ShortTermMemory | None = None,
) -> ObjectiveState:
    """Track the grand goal spanning across OODA epochs.

    Reads progress from Tier 4 Short-Term Memory and updates
    the objective state accordingly.
    """
    # Read progress from STM if available
    progress = 0.0
    sub_completed = 0
    sub_total = 0

    if stm is not None:
        context = stm.read_context()
        for snapshot in context.dag_snapshots:
            sub_total += snapshot.total_nodes
            sub_completed += snapshot.completed_count
        if sub_total > 0:
            progress = (sub_completed / sub_total) * 100.0

    status = ObjectiveStatus.PENDING
    if objective.completed:
        status = ObjectiveStatus.COMPLETED
    elif progress > 0:
        status = ObjectiveStatus.IN_PROGRESS

    state = ObjectiveState(
        objective_id=objective.objective_id,
        description=objective.description,
        status=status,
        progress_percentage=round(progress, 2),
        sub_objectives_completed=sub_completed,
        sub_objectives_total=sub_total,
    )

    log.debug(
        "Objective tracked",
        objective_id=objective.objective_id,
        status=status.value,
        progress=round(progress, 2),
    )

    return state


# ============================================================================
# Step 5: Sleep / Wake / Panic Control
# ============================================================================


async def control_sleep_wake(
    signal: LifecycleSignal,
    current_phase: LifecyclePhase,
) -> LifecycleState:
    """Control the agent's lifecycle state transitions.

    Handles START, PAUSE, PANIC, TERMINATE, and RESUME signals.
    """
    transition_map: dict[
        tuple[LifecyclePhase, LifecycleSignalType], LifecyclePhase
    ] = {
        # From INITIALIZING
        (LifecyclePhase.INITIALIZING, LifecycleSignalType.START): LifecyclePhase.ACTIVE,
        (LifecyclePhase.INITIALIZING, LifecycleSignalType.TERMINATE): LifecyclePhase.TERMINATED,
        # From ACTIVE
        (LifecyclePhase.ACTIVE, LifecycleSignalType.PAUSE): LifecyclePhase.SUSPENDED,
        (LifecyclePhase.ACTIVE, LifecycleSignalType.PANIC): LifecyclePhase.PANICKING,
        (LifecyclePhase.ACTIVE, LifecycleSignalType.TERMINATE): LifecyclePhase.TERMINATED,
        # From SUSPENDED
        (LifecyclePhase.SUSPENDED, LifecycleSignalType.RESUME): LifecyclePhase.ACTIVE,
        (LifecyclePhase.SUSPENDED, LifecycleSignalType.TERMINATE): LifecyclePhase.TERMINATED,
        # From PANICKING
        (LifecyclePhase.PANICKING, LifecycleSignalType.RESUME): LifecyclePhase.ACTIVE,
        (LifecyclePhase.PANICKING, LifecycleSignalType.TERMINATE): LifecyclePhase.TERMINATED,
        # From SLEEPING
        (LifecyclePhase.SLEEPING, LifecycleSignalType.RESUME): LifecyclePhase.ACTIVE,
        (LifecyclePhase.SLEEPING, LifecycleSignalType.START): LifecyclePhase.ACTIVE,
        (LifecyclePhase.SLEEPING, LifecycleSignalType.TERMINATE): LifecyclePhase.TERMINATED,
    }

    key = (current_phase, signal.signal_type)
    new_phase = transition_map.get(key, current_phase)

    state = LifecycleState(
        phase=new_phase,
        previous_phase=current_phase,
        reason=signal.reason or f"Signal: {signal.signal_type.value}",
        transitioned_utc=_now_utc(),
    )

    log.info(
        "Lifecycle transition",
        from_phase=current_phase.value,
        to_phase=new_phase.value,
        signal=signal.signal_type.value,
        reason=signal.reason,
    )

    return state


# ============================================================================
# Step 6: Commit Epoch Memory
# ============================================================================


async def commit_epoch_memory(
    stm: ShortTermMemory,
) -> EpochSummary:
    """Persist epoch to Vault by flushing Short-Term Memory.

    In production, the summary is sent to the Vault Service via HTTP API.
    The kernel handles the flush; the service layer handles persistence.
    """
    summary = stm.flush_to_summarizer()

    log.info(
        "Epoch memory committed",
        epoch_id=summary.epoch_id,
        dags_processed=len(summary.dag_ids_processed),
        events_processed=summary.total_events_processed,
    )

    return summary


# ============================================================================
# Top-Level Lifecycle Runner
# ============================================================================


async def run_lifecycle(spawn_request: SpawnRequest) -> Result:
    """Top-level lifecycle runner.

    Initializes the agent, loads its profile, sets identity constraints,
    and prepares the lifecycle report. The actual OODA loop execution
    is handled by Tier 4 — this function manages the macro lifecycle.
    """
    ref = _ref("run_lifecycle")
    start = time.perf_counter()

    try:
        # Step 1: Genesis
        identity = await initialize_agent(spawn_request)

        # Step 2: Load profile
        profile = await load_cognitive_profile(spawn_request.profile_id)

        # Step 3: Set constraints
        identity_ctx = set_identity_constraints(identity.agent_id, profile)

        # Step 4: Initial lifecycle state
        lifecycle_state = await control_sleep_wake(
            LifecycleSignal(
                signal_type=LifecycleSignalType.START,
                reason="Agent genesis complete",
            ),
            current_phase=LifecyclePhase.INITIALIZING,
        )

        # Build lifecycle report
        lifecycle = AgentLifecycle(
            agent_id=identity.agent_id,
            identity=identity,
            final_phase=lifecycle_state.phase,
        )

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)

        signal = create_data_signal(
            data={
                "lifecycle": lifecycle.model_dump(),
                "identity_context": {
                    "agent_id": identity_ctx.agent_id,
                    "role": identity_ctx.role,
                    "skills": list(identity_ctx.skills),
                    "quality_bar": identity_ctx.quality_bar,
                },
            },
            schema="AgentLifecycle",
            origin=ref,
            trace_id="",
            tags={
                "agent_id": identity.agent_id,
                "role": identity.role,
                "phase": lifecycle_state.phase.value,
            },
        )

        log.info(
            "Lifecycle initialized",
            agent_id=identity.agent_id,
            role=identity.role,
            phase=lifecycle_state.phase.value,
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Lifecycle initialization failed: {exc}",
            source=ref,
            detail={"request_id": spawn_request.request_id, "error_type": type(exc).__name__},
        )
        log.error("Lifecycle initialization failed", error=str(exc))
        return fail(error=error, metrics=metrics)
