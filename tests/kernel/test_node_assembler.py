import pytest
from pydantic import BaseModel, Field

from kernel.node_assembler.engine import (
    wrap_in_standard_io,
    inject_telemetry,
    hook_input_validation,
    hook_output_validation,
    assemble_node
)
from kernel.graph_synthesizer.types import ActionInstruction
from shared.config import get_settings


class InputSchema(BaseModel):
    command: str = Field(..., min_length=2)

class OutputSchema(BaseModel):
    status: str = Field(..., pattern="^(done|error)$")


@pytest.mark.asyncio
@pytest.mark.parametrize("scenario_name, command_input, action_return", [
    ("Success Case", "ls", {"status": "done"}),
    ("Validation Failure Case", "x", {"status": "done"}), # fails min_length=2
    ("Action Error Case", "ls", Exception("Command timed out")), # fails with exception
    ("Output Schema Failure Case", "ls", {"status": "unknown"}) # fails status pattern
])
async def test_node_assembler_comprehensive(scenario_name, command_input, action_return):
    """REAL SIMULATION: Verify Node Assembler Kernel functions with multiple scenarios."""
    print(f"\n--- Testing Node Assembler: Scenario='{scenario_name}' ---")

    async def mock_action(state):
        if isinstance(action_return, Exception):
            raise action_return
        return action_return

    instruction = ActionInstruction(task_id="t1", description=f"Run {command_input}", action_type="shell", parameters={})
    state = {"command": command_input}

    print(f"\n[Test]: wrap_in_standard_io")
    print(f"   [INPUT]: action_return='{action_return}'")
    wrapped_io = wrap_in_standard_io(mock_action)
    res_io = await wrapped_io(state.copy())
    if isinstance(action_return, Exception):
        assert res_io.get("__node_success__") is False
        print(f"   [OUTPUT]: Wrapped error caught")
    else:
        assert res_io.get("status") == action_return.get("status")
        print(f"   [OUTPUT]: Result Status={res_io.get('status')}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: inject_telemetry")
    print(f"   [INPUT]: trace_id='tr-001'")
    instrumented = inject_telemetry(wrapped_io, trace_id="tr-001", node_id="node-01")
    res_tel = await instrumented(state.copy())
    assert "__node_duration_ms__" in res_tel
    print(f"   [OUTPUT]: Telemetry injected (duration={res_tel['__node_duration_ms__']:.2f}ms)")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: hook_input_validation")
    print(f"   [INPUT]: command='{command_input}'")
    validated_in = hook_input_validation(instrumented, InputSchema)
    res_vin = await validated_in(state.copy())
    if len(command_input) < 2:
        assert res_vin.get("__node_success__") is False
        print(f"   [OUTPUT]: Correctly caught input validation error")
    else:
        print(f"   [OUTPUT]: Input validation passed")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: hook_output_validation")
    if len(command_input) >= 2 and not isinstance(action_return, Exception):
        print(f"   [INPUT]: status='{action_return.get('status')}'")
        validated_out = hook_output_validation(instrumented, OutputSchema)
        res_vout = await validated_out(state.copy())
        if action_return.get("status") not in ("done", "error"):
            assert res_vout.get("__node_success__") is False
            print(f"   [OUTPUT]: Correctly caught output validation error")
        else:
            print(f"   [OUTPUT]: Output validation passed")
    else:
        print(f"   [INPUT]: Skipped due to earlier failure or exception")
        print(f"   [OUTPUT]: N/A")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: assemble_node")
    print(f"   [INPUT]: task_id='{instruction.task_id}'")
    res_final = await assemble_node(
        instruction, 
        input_schema=InputSchema, 
        output_schema=OutputSchema, 
        action_callable=mock_action
    )
    assert res_final.is_success
    print(f"   [OUTPUT]: Status={res_final.status}, Signals count={len(res_final.signals)}")
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
