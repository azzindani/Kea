"""
Tier 3: Node Assembler Module.

Factory that wraps raw action callables into executable DAG nodes
with standard I/O, telemetry, and schema validation layers.

Usage::

    from kernel.node_assembler import assemble_node
    from kernel.graph_synthesizer import ActionInstruction

    instruction = ActionInstruction(task_id="t1", description="Query DB")
    result = await assemble_node(instruction)
"""

from .engine import (
    assemble_node,
    hook_input_validation,
    hook_output_validation,
    inject_telemetry,
    wrap_in_standard_io,
)
from .types import (
    AssemblyConfig,
    AssemblyReport,
    CallableDescriptor,
)

__all__ = [
    "assemble_node",
    "wrap_in_standard_io",
    "inject_telemetry",
    "hook_input_validation",
    "hook_output_validation",
    "AssemblyConfig",
    "AssemblyReport",
    "CallableDescriptor",
]
