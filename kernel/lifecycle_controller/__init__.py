"""
Tier 5: Lifecycle Controller Module.

Agent lifecycle management: genesis, identity, sleep/wake/panic
transitions, macro-objective tracking, and epoch memory commits.

Usage::

    from kernel.lifecycle_controller import run_lifecycle, SpawnRequest

    request = SpawnRequest(request_id="req_001", role="analyst")
    result = await run_lifecycle(request)
"""

from .engine import (
    commit_epoch_memory,
    control_sleep_wake,
    initialize_agent,
    load_cognitive_profile,
    run_lifecycle,
    set_identity_constraints,
    track_macro_objective,
)
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

__all__ = [
    # Engine functions
    "run_lifecycle",
    "initialize_agent",
    "load_cognitive_profile",
    "set_identity_constraints",
    "track_macro_objective",
    "control_sleep_wake",
    "commit_epoch_memory",
    # Types
    "SpawnRequest",
    "AgentIdentity",
    "CognitiveProfile",
    "IdentityContext",
    "LifecyclePhase",
    "LifecycleSignal",
    "LifecycleSignalType",
    "LifecycleState",
    "ObjectiveState",
    "ObjectiveStatus",
    "AgentLifecycle",
]
