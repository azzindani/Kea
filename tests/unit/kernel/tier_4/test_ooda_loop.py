from unittest.mock import AsyncMock, MagicMock

import pytest

from kernel.graph_synthesizer.types import (
    ActionInstruction,
    DAGState,
    ExecutableDAG,
    ExecutableNode,
    NodeStatus,
)
from kernel.ooda_loop.engine import (
    decide,
    observe,
    orient,
)
from kernel.ooda_loop.types import (
    DecisionAction,
    EventStream,
    MacroObjective,
    ObservationEvent,
    OrientedState,
)
from kernel.short_term_memory.engine import ShortTermMemory
from kernel.short_term_memory.types import EventSource
from shared.inference_kit import InferenceKit


@pytest.mark.asyncio
async def test_observe():
    stm = ShortTermMemory()
    stream = EventStream(stream_id="test")
    events = [ObservationEvent(event_id="e1", source=EventSource.SYSTEM, description="test", payload={})]

    obs = await observe(stream, stm, events)
    assert len(obs) == 1
    assert stm.history.events[0].event_id == "e1"


@pytest.mark.asyncio
async def test_orient():
    stm = ShortTermMemory()
    obs = [ObservationEvent(event_id="e1", source=EventSource.SYSTEM, description="Database is disconnected", payload={"key": "val"})]

    oriented = await orient(obs, stm)

    assert oriented.is_blocked
    assert "disconnected" in oriented.blocking_reason.lower()

    context = await stm.read_context()
    assert context.cached_entities.get("system_key") == "val"


@pytest.mark.asyncio
async def test_decide():
    oriented = OrientedState(is_blocked=False, blocking_reason="", enriched_context={}, observation_summary="", state_changes=[])
    obj = MacroObjective(description="Test objective", completed=False)

    # No DAG
    dec = await decide(oriented, [obj], None, None)
    assert dec.action == DecisionAction.REPLAN

    # Blocked
    oriented_blocked = OrientedState(is_blocked=True, blocking_reason="test", enriched_context={}, observation_summary="", state_changes=[])
    dec2 = await decide(oriented_blocked, [obj], None, None)
    assert dec2.action == DecisionAction.PARK

    # DAG pending
    node = ExecutableNode(node_id="n1", instruction=ActionInstruction(task_id="t1", description="", action_type="", required_skills=[], required_tools=[], parameters={}), input_keys=[], output_keys=[], parallelizable=False, status=NodeStatus.PENDING)
    dag = ExecutableDAG(dag_id="d1", description="", nodes=[node], edges=[], entry_node_ids=["n1"], terminal_node_ids=[], state=DAGState(pending_nodes=["n1"]), execution_order=[], parallel_groups=[["n1"]], has_external_calls=False, has_state_mutations=False)

    dec3 = await decide(oriented, [obj], dag, None)
    assert dec3.action == DecisionAction.CONTINUE
    assert "n1" in dec3.target_node_ids


@pytest.mark.asyncio
async def test_llm_fallback_orient():
    kit = MagicMock(spec=InferenceKit)
    kit.has_llm = True

    mock_resp = MagicMock()
    mock_resp.content = '```json\n{"is_blocked": true, "blocking_reason": "Firewall", "summary": "Firewall blocked access"}\n```'

    kit.llm = AsyncMock()
    kit.llm.complete.return_value = mock_resp
    kit.llm_config = MagicMock()

    stm = ShortTermMemory()
    obs = [ObservationEvent(event_id="e1", source=EventSource.SYSTEM, description="Connection dropped", payload={})]

    oriented = await orient(obs, stm, kit=kit)

    assert oriented.is_blocked
    assert oriented.blocking_reason == "Firewall"
    assert oriented.observation_summary == "Firewall blocked access"
