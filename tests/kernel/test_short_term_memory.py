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
    from kernel.short_term_memory.types import EventSource
    event = ObservationEvent(
        event_id="evt-test",
        source=EventSource.USER,
        description=event_description
    )
    stm.push_event(event)
    assert len(stm.get_recent_events()) > 0
    print(f"   Event History Count: {len(stm.get_recent_events())}")
    print("[SUCCESS]")

    print("\n[Test]: cache_entity")
    entity_id = "ent-001"
    entity_val = {"type": "user_pref", "value": "dark_mode"}
    stm.cache_entity(entity_id, entity_val)
    # Testing internal cache
    print(f"   Outcome: Entity '{entity_id}' cached")
    print("[SUCCESS]")

    print("\n[Test]: update_dag_state")
    dag_id = "dag-99"
    # Need to register first
    stm.register_dag(dag_id, ["node-3"])
    stm.update_dag_state(dag_id, "node-3", NodeExecutionStatus.COMPLETED)
    snapshot = stm.get_dag_snapshot(dag_id)
    assert snapshot.completion_percentage == 100.0
    print(f"   Outcome: DAG '{dag_id}' updated to COMPLETED")
    print("[SUCCESS]")

    print("\n[Test]: read_context")
    oriented_ctx = await stm.read_context()
    assert oriented_ctx is not None
    assert len(oriented_ctx.recent_events) > 0
    print(f"   Context Sliced: {len(oriented_ctx.recent_events)} events included")
    print("[SUCCESS]")

    print("\n[Test]: flush_to_summarizer")
    summary = stm.flush_to_summarizer()
    assert summary is not None
    assert summary.epoch_id.startswith("epoch-")
    print(f"   Epoch ID: {summary.epoch_id}")
    print("[SUCCESS]")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
