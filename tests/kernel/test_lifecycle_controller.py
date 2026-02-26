import pytest

from kernel.lifecycle_controller.engine import (
    initialize_agent,
    load_cognitive_profile,
    set_identity_constraints,
    track_macro_objective,
    control_sleep_wake,
    commit_epoch_memory,
    run_lifecycle
)
from kernel.lifecycle_controller.types import (
    SpawnRequest, LifecycleSignal, LifecycleSignalType, LifecyclePhase
)
from kernel.ooda_loop.types import MacroObjective
from kernel.short_term_memory import ShortTermMemory
from shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.parametrize("role, profile_id", [
    ("CEO", "p_ceo_001"),
    ("Senior Engineer", "p_eng_99"),
    ("Support Intern", "p_intern_generic"),
    ("Security Auditor", "p_audit_strict")
])
async def test_lifecycle_controller_comprehensive(role, profile_id):
    """REAL SIMULATION: Verify Lifecycle Controller Kernel functions with multiple agent scenarios."""
    print(f"\n--- Testing Lifecycle Controller: Role='{role}', Profile='{profile_id}' ---")

    spawn_req = SpawnRequest(role=role, profile_id=profile_id)

    print(f"\n[Test]: initialize_agent")
    print(f"   [INPUT]: role='{role}', profile='{profile_id}'")
    identity = await initialize_agent(spawn_req)
    assert identity.agent_id.startswith("agt_")
    assert identity.role == role
    print(f"   [OUTPUT]: Agent ID={identity.agent_id}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: load_cognitive_profile")
    print(f"   [INPUT]: profile_id='{profile_id}'")
    profile = await load_cognitive_profile(profile_id)
    assert profile.profile_id == profile_id
    print(f"   [OUTPUT]: Role Name={profile.role_name}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: set_identity_constraints")
    print(f"   [INPUT]: agent_id='{identity.agent_id}'")
    identity_ctx = set_identity_constraints(identity.agent_id, profile)
    assert identity_ctx.agent_id == identity.agent_id
    print(f"   [OUTPUT]: Identity Constraints set for {identity_ctx.role}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: track_macro_objective")
    macro_obj = MacroObjective(objective_id="obj_alpha", description=f"Goal for {role}")
    print(f"   [INPUT]: objective_id='{macro_obj.objective_id}'")
    obj_state = track_macro_objective(macro_obj)
    assert obj_state.objective_id == "obj_alpha"
    print(f"   [OUTPUT]: Progress={obj_state.progress_percentage}%")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: control_sleep_wake")
    sig_start = LifecycleSignal(signal_type=LifecycleSignalType.START, reason="Initialization Success")
    print(f"   [INPUT]: phase={LifecyclePhase.INITIALIZING}, signal={sig_start.signal_type}")
    life_state = await control_sleep_wake(sig_start, LifecyclePhase.INITIALIZING)
    assert life_state.phase == LifecyclePhase.ACTIVE
    print(f"   [OUTPUT]: Current Phase={life_state.phase.value}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: commit_epoch_memory")
    stm = ShortTermMemory()
    print(f"   [INPUT]: STM items_count={len(stm.items) if hasattr(stm, 'items') else 0}")
    epoch_summary = await commit_epoch_memory(stm)
    assert epoch_summary.epoch_id.startswith("epoch")
    print(f"   [OUTPUT]: Epoch ID={epoch_summary.epoch_id}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: run_lifecycle")
    print(f"   [INPUT]: role='{role}'")
    res = await run_lifecycle(spawn_req)
    assert res.is_success
    print(f"   [OUTPUT]: Status={res.status}, Signals count={len(res.signals)}")
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
