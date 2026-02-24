from unittest.mock import AsyncMock, MagicMock

import pytest

from kernel.short_term_memory.engine import ShortTermMemory
from kernel.short_term_memory.types import (
    EventSource,
    NodeExecutionStatus,
    ObservationEvent,
)
from shared.inference_kit import InferenceKit


def test_dag_state_tracking():
    stm = ShortTermMemory()

    stm.register_dag("dag1", ["n1", "n2"])
    snap = stm.get_dag_snapshot("dag1")
    assert snap.total_nodes == 2
    assert snap.pending_count == 2
    assert snap.completion_percentage == 0.0

    snap2 = stm.update_dag_state("dag1", "n1", NodeExecutionStatus.COMPLETED)
    assert snap2.completed_count == 1
    assert snap2.pending_count == 1
    assert snap2.completion_percentage == 50.0

    snap3 = stm.update_dag_state("dag1", "n2", NodeExecutionStatus.FAILED)
    assert snap3.failed_count == 1
    assert "n2" in snap3.failed_node_ids


def test_event_history(monkeypatch):
    class MockSettings:
        stm_max_events: int = 2
        stm_max_entities: int = 100
        stm_default_entity_ttl_seconds: int = 60
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.short_term_memory.engine.get_settings", lambda: MockKernelSettings())

    stm = ShortTermMemory()
    stm.push_event(ObservationEvent(event_id="e1", source=EventSource.SYSTEM, description="1", payload={}))
    stm.push_event(ObservationEvent(event_id="e2", source=EventSource.SYSTEM, description="2", payload={}))
    stm.push_event(ObservationEvent(event_id="e3", source=EventSource.SYSTEM, description="3", payload={}))

    events = stm.get_recent_events()
    assert len(events) == 2
    assert events[0].event_id == "e3"
    assert events[1].event_id == "e2"


def test_entity_cache(monkeypatch):
    class MockSettings:
        stm_default_entity_ttl_seconds: int = 60
        stm_max_events: int = 100
        stm_max_entities: int = 2
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.short_term_memory.engine.get_settings", lambda: MockKernelSettings())

    stm = ShortTermMemory()
    stm.cache_entity("k1", "v1")
    stm.cache_entity("k2", "v2")
    stm.cache_entity("k3", "v3")

    assert stm.get_entity("k1") is None
    assert stm.get_entity("k2") == "v2"
    assert stm.get_entity("k3") == "v3"

    stm.cache_entity("k4", "v4", ttl=-1)
    assert stm.get_entity("k4") is None


@pytest.mark.asyncio
async def test_llm_fallback_read_context(monkeypatch):
    class MockSettings:
        stm_default_entity_ttl_seconds: int = 60
        stm_max_events: int = 100
        stm_max_entities: int = 100
        stm_context_max_items: int = 5
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.short_term_memory.engine.get_settings", lambda: MockKernelSettings())

    kit = MagicMock(spec=InferenceKit)
    kit.has_embedder = True
    kit.embedder = AsyncMock()
    kit.embedder.embed.side_effect = lambda text: [1.0, 0.0] if "test" in str(text) else [0.0, 1.0]

    stm = ShortTermMemory()
    stm.cache_entity("k1", "apple")
    stm.cache_entity("k2", "test data")

    ctx = await stm.read_context(query="test", kit=kit)

    assert "k2" in ctx.cached_entities
