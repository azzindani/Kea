import pytest

from kernel.async_multitasking.engine import check_async_requirement, switch_context
from kernel.async_multitasking.types import DAGQueue, DAGQueueEntry
from kernel.ooda_loop.types import ActionResult


def test_check_async_requirement():
    ar = ActionResult(node_id="n1", job_id="123")
    assert check_async_requirement(ar)

    ar2 = ActionResult(node_id="n1", content="done")
    assert not check_async_requirement(ar2)

@pytest.mark.asyncio
async def test_switch_context():
    q = DAGQueue(entries=[
        DAGQueueEntry(dag_id="d1", is_parked=True, description="d1"),
        DAGQueueEntry(dag_id="d2", is_parked=False, priority=10, description="d2"),
        DAGQueueEntry(dag_id="d3", is_parked=False, priority=5, description="d3")
    ])

    best = await switch_context(q)
    assert best == "d3"
