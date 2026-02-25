from unittest.mock import AsyncMock, MagicMock

import pytest

from kernel.graph_synthesizer.engine import (
    calculate_dependency_edges,
    compile_dag,
    map_subtasks_to_nodes,
)
from kernel.graph_synthesizer.types import (
    ActionInstruction,
    Edge,
    EdgeKind,
    ExecutableNode,
    NodeStatus,
)
from kernel.task_decomposition.types import SubTaskItem
from shared.inference_kit import InferenceKit


@pytest.mark.asyncio
async def test_map_subtasks_to_nodes():
    tasks = [
        SubTaskItem(
            id="t1",
            description="analyze the data",
            domain="general",
            required_skills=[],
            required_tools=[],
            depends_on=[],
            inputs=[],
            outputs=["out1"],
            parallelizable=False,
        )
    ]

    nodes = await map_subtasks_to_nodes(tasks)
    assert len(nodes) == 1
    assert nodes[0].instruction.action_type == "llm_inference"
    assert "out1" in nodes[0].output_keys


def test_calculate_dependency_edges():
    nodes = [
        ExecutableNode(
            node_id="n1",
            instruction=ActionInstruction(task_id="t1", description="", action_type="", required_skills=[], required_tools=[], parameters={}),
            input_keys=[],
            output_keys=["data"],
            parallelizable=False,
            status=NodeStatus.PENDING,
        ),
        ExecutableNode(
            node_id="n2",
            instruction=ActionInstruction(task_id="t2", description="", action_type="", required_skills=[], required_tools=[], parameters={}),
            input_keys=["data"],
            output_keys=["result"],
            parallelizable=False,
            status=NodeStatus.PENDING,
        ),
    ]

    edges = calculate_dependency_edges(nodes)
    assert len(edges) == 1
    assert edges[0].from_node_id == "n1"
    assert edges[0].to_node_id == "n2"
    assert edges[0].data_key == "data"


def test_compile_dag(monkeypatch):
    class MockSettings:
        max_parallel_branches: int = 2
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.graph_synthesizer.engine.get_settings", lambda: MockKernelSettings())

    nodes = [
        ExecutableNode(
            node_id="n1",
            instruction=ActionInstruction(task_id="t1", description="create db", action_type="tool_call", required_skills=[], required_tools=[], parameters={}),
            input_keys=[],
            output_keys=[],
            parallelizable=False,
            status=NodeStatus.PENDING
        ),
        ExecutableNode(
            node_id="n2",
            instruction=ActionInstruction(task_id="t2", description="read db", action_type="general", required_skills=[], required_tools=[], parameters={}),
            input_keys=[],
            output_keys=[],
            parallelizable=False,
            status=NodeStatus.PENDING
        ),
    ]
    edges = [
        Edge(from_node_id="n1", to_node_id="n2", kind=EdgeKind.SEQUENTIAL, data_key="db")
    ]

    dag = compile_dag(nodes, edges, "Test objective")

    assert dag.has_external_calls
    assert dag.has_state_mutations
    assert len(dag.nodes) == 2
    assert "n1" in dag.entry_node_ids
    assert "n2" in dag.terminal_node_ids


@pytest.mark.asyncio
async def test_llm_fallback_map_subtasks(monkeypatch):
    kit = MagicMock(spec=InferenceKit)
    kit.has_llm = True

    mock_resp = MagicMock()
    mock_resp.content = '```json\n{"action_type": "advanced_tool"}\n```'

    kit.llm = AsyncMock()
    kit.llm.complete.return_value = mock_resp
    kit.llm_config = MagicMock()

    tasks = [SubTaskItem(
        id="t1",
        description="Do weird thing",
        domain="gen",
        required_skills=[],
        required_tools=[],
        depends_on=[],
        inputs=[],
        outputs=[],
        parallelizable=False
    )]

    nodes = await map_subtasks_to_nodes(tasks, kit=kit)

    assert len(nodes) == 1
    assert nodes[0].instruction.action_type == "advanced_tool"
