from typing import Any

import pytest
from pydantic import BaseModel

from kernel.graph_synthesizer.types import ActionInstruction
from kernel.node_assembler.engine import (
    assemble_node,
    hook_input_validation,
    hook_output_validation,
    inject_telemetry,
    wrap_in_standard_io,
)


class DummySchema(BaseModel):
    key: str


@pytest.mark.asyncio
async def test_wrap_in_standard_io():
    async def failing_fn(state: dict[str, Any]) -> dict[str, Any]:
        raise ValueError("Intentional crash")

    wrapped = wrap_in_standard_io(failing_fn)

    state = {}
    res = await wrapped(state)

    assert res.get("__node_success__") is False
    assert "Intentional crash" in res.get("__node_error__", {}).get("message", "")


@pytest.mark.asyncio
async def test_inject_telemetry():
    async def normal_fn(state: dict[str, Any]) -> dict[str, Any]:
        return state

    instrumented = inject_telemetry(normal_fn, "trace1", "dag1", "node1")

    res = await instrumented({"__node_success__": True})
    assert "__node_duration_ms__" in res


@pytest.mark.asyncio
async def test_hook_input_validation():
    # Mock decorator incorrectly applied in source (needs fixing wrapper args?), but let's test behavior assuming implementation holds
    async def normal_fn(state: dict[str, Any]) -> dict[str, Any]:
        state["processed"] = True
        return state

    validated = hook_input_validation(normal_fn, DummySchema)

    # Missing 'key'
    res = await validated({})
    assert res.get("__node_success__") is False
    assert "processed" not in res

    # Valid
    res2 = await validated({"key": "value"})
    assert res2.get("processed") is True


@pytest.mark.asyncio
async def test_hook_output_validation():
    async def normal_fn(state: dict[str, Any]) -> dict[str, Any]:
        return {"wrong_key": "val"}

    validated = hook_output_validation(normal_fn, DummySchema)

    res = await validated({})
    assert res.get("__node_success__") is False
    assert "wrong_key" in res


@pytest.mark.asyncio
async def test_assemble_node():
    instruction = ActionInstruction(
        task_id="t1",
        description="Just passthrough",
        action_type="general",
        required_skills=[],
        required_tools=[],
        parameters={}
    )

    # Assemble with no callable creates a passthrough
    res = await assemble_node(instruction)
    assert res.is_success
    data = res.unwrap()
    assert len(data.signals) == 1

    # Data is an ExecutableNode structure, but we only have standard result
    node_data = data.signals[0].body["data"]
    assert "node_id" in node_data
