import pytest

from kernel.short_term_memory.engine import (
    ShortTermMemory,
    update_dag_state,
    index_memory_event,
    cache_entity,
    slice_context_for_orient,
    flush_to_summarizer,
    run_memory_cycle
)
from shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.parametrize("event_description, importance_level", [
    ("User requested a system health check", "normal"),
    ("System detected a potential intrusion in sector 4", "critical"),
    ("Automated backup completed successfully", "low"),
    ("User corrected a previous instruction", "high")
])
async def test_short_term_memory_comprehensive(event_description, importance_level):
    """REAL SIMULATION: Verify Short-Term Memory Kernel functions with multiple events."""
    print(f"\n--- Testing Short-Term Memory: Event='{event_description}', Importance={importance_level} ---")

    stm = ShortTermMemory()
    metadata = {"importance": importance_level, "source": "test_suite"}

    print(f"\n[Test]: index_memory_event")
    index_memory_event(stm, event_description, metadata)
    assert len(stm.event_history) > 0
    print(f"   Event History Count: {len(stm.event_history)}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: cache_entity")
    entity_id = "ent-001"
    entity_val = {"type": "user_pref", "value": "dark_mode"}
    cache_entity(stm, entity_id, entity_val)
    assert entity_id in stm.entity_cache
    print(f"   Outcome: Entity '{entity_id}' cached")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: update_dag_state")
    dag_id = "dag-99"
    update_dag_state(stm, dag_id, "RUNNING", {"active_node": "node-3"})
    assert dag_id in stm.active_dags
    print(f"   Outcome: DAG '{dag_id}' updated to RUNNING")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: slice_context_for_orient")
    oriented_ctx = slice_context_for_orient(stm)
    assert oriented_ctx is not None
    assert len(oriented_ctx.recent_events) > 0
    print(f"   Context Sliced: {len(oriented_ctx.recent_events)} events included")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: run_memory_cycle")
    # Test adding another event via orchestrator
    res = await run_memory_cycle(stm, "index", "Secondary event", {"id": 2})
    assert res.is_success
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: flush_to_summarizer")
    epoch_summary = flush_to_summarizer(stm)
    assert epoch_summary is not None
    assert hasattr(epoch_summary, 'epoch_id')
    print(f"   Epoch ID: {epoch_summary.epoch_id}")
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
