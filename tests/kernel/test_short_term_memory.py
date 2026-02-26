import pytest

from kernel.short_term_memory.engine import (
    ShortTermMemory,
)
from kernel.short_term_memory.types import ObservationEvent, NodeExecutionStatus


@pytest.mark.asyncio
@pytest.mark.parametrize("event_description, importance_level", [
    ("User requested a system health check", "normal"),
    ("System detected a potential intrusion in sector 4", "critical"),
    ("Automated backup completed successfully", "low"),
    ("User corrected a previous instruction", "high"),
])
async def test_short_term_memory_comprehensive(event_description, importance_level):
    """REAL SIMULATION: Verify Short-Term Memory Kernel functions with multiple events."""
    print(f"\n--- Testing Short-Term Memory: Event='{event_description}' ---")

    stm = ShortTermMemory()

    print("\n[Test]: push_event")
    print(f"   [INPUT]: event='{event_description[:30]}...', importance='{importance_level}'")
    from kernel.short_term_memory.types import EventSource
    event = ObservationEvent(
        event_id="evt-test",
        source=EventSource.USER,
        description=event_description
    )
    stm.push_event(event)
    events = stm.get_recent_events()
    assert len(events) > 0
    print(f"   [OUTPUT]: Event History Count={len(events)}")
    print("[SUCCESS]")

    print("\n[Test]: cache_entity")
    entity_id = "ent-001"
    entity_val = {"type": "user_pref", "value": "dark_mode"}
    print(f"   [INPUT]: entity_id='{entity_id}', value='{entity_val['value']}'")
    stm.cache_entity(entity_id, entity_val)
    print(f"   [OUTPUT]: Outcome=Entity '{entity_id}' cached")
    print("[SUCCESS]")

    print("\n[Test]: update_dag_state")
    dag_id = "dag-99"
    print(f"   [INPUT]: dag_id='{dag_id}', status='{NodeExecutionStatus.COMPLETED.value}'")
    stm.register_dag(dag_id, ["node-3"])
    stm.update_dag_state(dag_id, "node-3", NodeExecutionStatus.COMPLETED)
    snapshot = stm.get_dag_snapshot(dag_id)
    assert snapshot.completion_percentage == 100.0
    print(f"   [OUTPUT]: Outcome=DAG '{dag_id}' updated to COMPLETED (Progress={snapshot.completion_percentage}%)")
    print("[SUCCESS]")

    print("\n[Test]: read_context")
    print(f"   [INPUT]: stm_size={len(stm.get_recent_events())}")
    oriented_ctx = await stm.read_context()
    assert oriented_ctx is not None
    assert len(oriented_ctx.recent_events) > 0
    print(f"   [OUTPUT]: Context Sliced={len(oriented_ctx.recent_events)} events included")
    print("[SUCCESS]")

    print("\n[Test]: flush_to_summarizer")
    print(f"   [INPUT]: flushing memory")
    summary = stm.flush_to_summarizer()
    assert summary is not None
    assert summary.epoch_id.startswith("epoch_")
    print(f"   [OUTPUT]: Epoch ID={summary.epoch_id}")
    print("[SUCCESS]")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
