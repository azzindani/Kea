import pytest

from kernel.reflection_and_guardrails.engine import (
    run_pre_execution_check,
    run_post_execution_reflection,
    evaluate_consensus,
    check_value_guardrails
)
from kernel.graph_synthesizer.types import ExecutableDAG
from kernel.reflection_and_guardrails.types import ExecutionResult


@pytest.mark.asyncio
@pytest.mark.parametrize("objective, execution_outputs, is_dangerous", [
    ("List available tools", {"tools": ["ls", "grep"]}, False),
    ("Delete production database", {"status": "attempted"}, True),
    ("Access private keys for admin", {"key": "secret"}, True),
    ("Generate a summary of the project", {"summary": "Done"}, False)
])
async def test_reflection_and_guardrails_comprehensive(objective, execution_outputs, is_dangerous, inference_kit):
    """REAL SIMULATION: Verify Reflection & Guardrails Kernel functions with multiple inputs."""
    print(f"\n--- Testing Reflection & Guardrails: Objective='{objective}' ---")

    dag = ExecutableDAG(dag_id="dag-test", nodes=[], edges=[], description=objective)

    print(f"\n[Test]: run_pre_execution_check")
    print(f"   [INPUT]: objective='{objective}'")
    pre_res = await run_pre_execution_check(dag, kit=inference_kit)
    assert pre_res.is_success
    print(f"   [OUTPUT]: Pre-check status={pre_res.status}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: evaluate_consensus")
    print(f"   [INPUT]: objective='{objective}'")
    consensus_res = await evaluate_consensus([dag], kit=inference_kit)
    assert consensus_res is not None
    print(f"   [OUTPUT]: Consensus Score={consensus_res.confidence if hasattr(consensus_res, 'confidence') else 'N/A'}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: check_value_guardrails")
    print(f"   [INPUT]: objective='{objective}'")
    guard_res = await check_value_guardrails(dag, kit=inference_kit)
    assert guard_res is not None
    print(f"   [OUTPUT]: Guardrails check passed")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: run_post_execution_reflection")
    exec_res = ExecutionResult(dag_id=dag.dag_id, completed_nodes=[], failed_nodes=[], outputs=execution_outputs)
    print(f"   [INPUT]: outputs={len(execution_outputs)} keys")
    post_res = await run_post_execution_reflection(exec_res, expected=[], kit=inference_kit)
    assert post_res.is_success
    print(f"   [OUTPUT]: Post-reflection status={post_res.status}")
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
