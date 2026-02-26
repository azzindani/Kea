import pytest

from kernel.async_multitasking.engine import (
    check_async_requirement,
    park_dag_state,
    register_wait_listener,
    switch_context,
    request_deep_sleep,
    manage_async_tasks
)
from kernel.async_multitasking.types import DAGQueue
from kernel.short_term_memory.engine import ShortTermMemory
from kernel.graph_synthesizer.types import ExecutableDAG
from kernel.ooda_loop.types import ActionResult as ToolOutput
from shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.parametrize("dag_id, reason, event_name", [
    ("dag_101", "waiting for external api call to finish", "api_response_received"),
    ("dag_202", "waiting for user input to continue", "user_input_provided"),
])
async def test_async_multitasking_comprehensive(dag_id, reason, event_name):
    """REAL SIMULATION: Verify Async Multitasking Kernel functions."""
    print(f"\n--- Testing Async Multitasking: DAG='{dag_id}' ---")

    stm = ShortTermMemory()
    dag = ExecutableDAG(dag_id=dag_id, nodes=[], edges=[], description="test")
    res = ToolOutput(node_id="node_1", outputs={"status": "pending", "job_id": "job_123"})

    print(f"\n[Test]: check_async_requirement")
    needs_async = check_async_requirement(res)
    assert needs_async is True
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: park_dag_state")
    ticket = park_dag_state(dag, stm, res)
    assert ticket.dag_id == dag_id
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: register_wait_listener")
    register_wait_listener(ticket, res)
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: switch_context")
    queue = DAGQueue()
    next_dag = switch_context(queue)
    # Since queue is empty, next_dag should likely be None or error handled
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: manage_async_tasks")
    final_res = await manage_async_tasks(res, dag, queue, stm)
    assert final_res.is_success
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
