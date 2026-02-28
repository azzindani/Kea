import pytest

from kernel.short_term_memory.engine import (
    ShortTermMemory,
)
from kernel.short_term_memory.types import ObservationEvent, NodeExecutionStatus


@pytest.mark.asyncio
@pytest.mark.parametrize("event_description, importance_level, payload", [
    ("User requested a system health check", "normal", {"client": "web-portal", "region": "us-east-1"}),
    ("System detected a potential intrusion in sector 4", "critical", {"alert_id": "SEC-909", "impact": "high", "nodes": ["k8s-master-01"]}),
    ("Automated backup completed successfully", "low", {"volume_id": "vol-01", "size_gb": 500}),
    ("Security policy updated by admin", "high", {"policy_id": "POL-X", "changes": ["disable_root_ssh"]}),
])
async def test_short_term_memory_comprehensive(event_description, importance_level, payload):
    """REAL SIMULATION: Verify Short-Term Memory Kernel functions with high-fidelity enterprise events."""
    print(f"\n--- Testing Short-Term Memory: Event='{event_description}' ---")

    stm = ShortTermMemory()

    print("\n[Test]: push_event")
    print(f"   [INPUT]: event='{event_description}', importance='{importance_level}', payload_keys={list(payload.keys())}")
    from kernel.short_term_memory.types import EventSource
    event = ObservationEvent(
        event_id="evt-real-001",
        source=EventSource.SYSTEM,
        description=event_description,
        payload=payload,
        priority=10 if importance_level == "critical" else 1
    )
    stm.push_event(event)
    events = stm.get_recent_events()
    assert len(events) > 0
    assert events[0].payload == payload
    print(f"   [OUTPUT]: Event History Count={len(events)} (Payload verified)")
    print("[SUCCESS]")

    print("\n[Test]: cache_spatiotemporal_entity")
    from kernel.location_and_time.types import SpatiotemporalBlock, TemporalRange, SpatialBounds
    from datetime import datetime
    
    entity_id = "context-anchor-01"
    st_block = SpatiotemporalBlock(
        temporal=TemporalRange(start=datetime.now(), end=datetime.now()),
        spatial=SpatialBounds(min_lat=35.6, max_lat=35.7, min_lon=139.6, max_lon=139.7, label="Tokyo Office"),
        fusion_confidence=0.98
    )
    
    print(f"   [INPUT]: entity_id='{entity_id}', spatial_label='{st_block.spatial.label}'")
    stm.cache_entity(entity_id, st_block)
    # Read back through context
    oriented_ctx = await stm.read_context()
    cached_val = oriented_ctx.cached_entities.get(entity_id)
    assert cached_val is not None
    assert cached_val.spatial.label == "Tokyo Office"
    print(f"   [OUTPUT]: Outcome=SpatiotemporalBlock entity cached and retrieved from context")
    print("[SUCCESS]")

    print("\n[Test]: update_dag_execution_state")
    dag_id = "dag-ent-909"
    print(f"   [INPUT]: dag_id='{dag_id}', status='{NodeExecutionStatus.COMPLETED.value}'")
    stm.register_dag(dag_id, ["node-security-scan"])
    stm.update_dag_state(dag_id, "node-security-scan", NodeExecutionStatus.COMPLETED)
    snapshot = stm.get_dag_snapshot(dag_id)
    assert snapshot.completion_percentage == 100.0
    print(f"   [OUTPUT]: Outcome=DAG '{dag_id}' Traceability verified (100% completion)")
    print("[SUCCESS]")

    print("\n[Test]: push_context_slice")
    print(f"   [INPUT]: stm_size={len(stm.get_recent_events())}")
    oriented_ctx = await stm.read_context()
    assert len(oriented_ctx.recent_events) > 0
    print(f"   [OUTPUT]: Context Sliced={len(oriented_ctx.recent_events)} events, {len(oriented_ctx.cached_entities)} entities")
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
