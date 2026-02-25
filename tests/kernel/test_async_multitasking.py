import pytest

from kernel.async_multitasking.engine import (
    park_dag,
    resume_dag,
    register_wait_listener,
    check_wait_listeners,
    request_deep_sleep,
    run_multitasking_manager
)
from shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.parametrize("dag_id, reason, event_name", [
    ("dag_101", "waiting for external api call to finish", "api_response_received"),
    ("dag_202", "waiting for user input to continue", "user_input_provided"),
    ("dag_303", "waiting for background compute task", "compute_task_done")
])
async def test_async_multitasking_comprehensive(dag_id, reason, event_name):
    """REAL SIMULATION: Verify Async Multitasking Kernel functions with multiple scenarios."""
    print(f"\n--- Testing Async Multitasking for {dag_id} (Reason: {reason}) ---")

    print(f"\n[Test]: park_dag")
    parked = park_dag(dag_id, reason)
    assert parked.dag_id == dag_id
    assert parked.reason == reason
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: register_wait_listener")
    register_wait_listener(dag_id, event_name)
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: check_wait_listeners")
    ready_dags = check_wait_listeners([event_name])
    assert dag_id in ready_dags
    print(f"   Dags ready for resume: {ready_dags}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: resume_dag")
    resumed = resume_dag(dag_id)
    assert resumed.dag_id == dag_id
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: request_deep_sleep")
    sleep_req = request_deep_sleep()
    assert sleep_req.requested is True
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: run_multitasking_manager")
    res = await run_multitasking_manager(dag_id, "park", reason)
    assert res.is_success
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
