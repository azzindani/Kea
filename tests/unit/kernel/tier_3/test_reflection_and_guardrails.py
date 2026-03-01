
import pytest

from kernel.advanced_planning.types import ExpectedOutcome
from kernel.graph_synthesizer.types import (
    ActionInstruction,
    DAGState,
    ExecutableDAG,
    ExecutableNode,
    NodeStatus,
)
from kernel.reflection_and_guardrails.engine import (
    check_value_guardrails,
    critique_execution,
    evaluate_consensus,
    optimize_loop,
)
from kernel.reflection_and_guardrails.types import (
    ExecutionResult,
)


@pytest.mark.asyncio
async def test_evaluate_consensus():
    # Testing the short-circuit (1 candidate)
    dag1 = ExecutableDAG(
        dag_id="dag1", description="", nodes=[], edges=[], entry_node_ids=[], terminal_node_ids=[],
        state=DAGState(pending_nodes=[]), execution_order=[], parallel_groups=[], has_external_calls=False, has_state_mutations=False
    )

    res = await evaluate_consensus([dag1])
    assert res.dag_id == "dag1"


@pytest.mark.asyncio
async def test_check_value_guardrails(monkeypatch):
    class MockSettings:
        guardrail_forbidden_actions: list[str] = ["delete_all", "drop_table"]
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.reflection_and_guardrails.engine.get_settings", lambda: MockKernelSettings())

    node1 = ExecutableNode(
        node_id="n1",
        instruction=ActionInstruction(task_id="t1", description="delete all files", action_type="general", required_skills=[], required_tools=[], parameters={}),
        input_keys=[], output_keys=[], parallelizable=False, status=NodeStatus.PENDING
    )

    dag = ExecutableDAG(
        dag_id="dag1", description="", nodes=[node1], edges=[], entry_node_ids=[], terminal_node_ids=[],
        state=DAGState(pending_nodes=[]), execution_order=[], parallel_groups=[], has_external_calls=False, has_state_mutations=False
    )

    res = await check_value_guardrails(dag)
    assert not res.passed
    assert len(res.violations) > 0


def test_critique_execution():
    result = ExecutionResult(
        dag_id="dag1",
        completed_nodes=["t1"],
        failed_nodes=[],
        outputs={"t1": {"status": "ok"}},
        duration_ms=100.0
    )

    expected = [
        ExpectedOutcome(
            task_id="t1",
            description="Should output ok",
            output_schema="",
            success_criteria={"success": True, "status": "ok"},
            confidence=0.9
        )
    ]

    critique = critique_execution(result, expected)

    assert critique.success_rate == 1.0
    assert critique.hypothesis_evaluations[0].met


def test_optimize_loop(monkeypatch):
    class MockSettings:
        reflection_min_score_gap: float = 0.5
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.reflection_and_guardrails.engine.get_settings", lambda: MockKernelSettings())

    result = ExecutionResult(
        dag_id="dag1",
        completed_nodes=[],
        failed_nodes=["t1"],
        outputs={},
        duration_ms=100.0
    )
    expected = [ExpectedOutcome(task_id="t1", description="", output_schema="", success_criteria={"success": True}, confidence=0.0)]

    critique = critique_execution(result, expected)

    opts = optimize_loop(critique)

    assert len(opts) > 0
    assert any("retry" in o.description.lower() for o in opts)
