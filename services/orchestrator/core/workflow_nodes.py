"""
Composable Workflow Node Types.

Defines n8n-style node primitives that can be assembled into arbitrary
workflow graphs. Each node type has a well-defined contract for inputs,
outputs, and execution semantics.

Node Types:
- ToolNode:    Calls a single MCP tool
- CodeNode:    Executes Python code
- LLMNode:     Makes an LLM reasoning call
- SwitchNode:  Conditional branching based on artifact values
- LoopNode:    Iterates over a list, spawning sub-tasks per item
- MergeNode:   Waits for all upstream branches, combines results
- AgenticNode: Autonomous goal-directed agent with inference-action-observe loop
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from shared.logging import get_logger

logger = get_logger(__name__)


class NodeType(str, Enum):
    """Workflow node type identifiers."""
    TOOL = "tool"
    CODE = "code"
    LLM = "llm"
    SWITCH = "switch"
    LOOP = "loop"
    MERGE = "merge"
    AGENTIC = "agentic"


class NodeStatus(str, Enum):
    """Execution status of a workflow node."""
    PENDING = "pending"
    WAITING = "waiting"     # Waiting for dependencies
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class NodeResult:
    """Standardized result from any node execution."""
    node_id: str
    status: NodeStatus
    output: Any = None
    artifacts: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    children_spawned: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowNode:
    """
    Base workflow node definition.

    All node types share these common fields. The `node_type` field
    determines which execution logic applies.
    """
    id: str
    node_type: NodeType
    phase: int = 1

    # Tool/execution configuration
    tool: str = ""
    args: dict[str, Any] = field(default_factory=dict)

    # Artifact wiring
    input_mapping: dict[str, str] = field(default_factory=dict)
    output_artifact: str | None = None

    # Dependencies (explicit)
    depends_on: list[str] = field(default_factory=list)

    # Execution state
    status: NodeStatus = NodeStatus.PENDING
    result: NodeResult | None = None
    retry_count: int = 0
    max_retries: int = 2

    # ---- Type-specific fields ----

    # SwitchNode
    condition: str = ""           # Expression to evaluate
    true_branch: list[dict] = field(default_factory=list)
    false_branch: list[dict] = field(default_factory=list)

    # LoopNode
    loop_over: str = ""           # Artifact reference to iterate
    loop_body: list[dict] = field(default_factory=list)
    max_parallel: int = 10
    loop_variable: str = "item"   # Variable name inside body

    # MergeNode
    merge_inputs: list[str] = field(default_factory=list)
    merge_strategy: str = "concat"  # concat | dict | first | custom

    # AgenticNode
    goal: str = ""
    agent_max_steps: int = 8
    agent_tools: list[str] = field(default_factory=list)

    # LLMNode
    llm_prompt: str = ""
    llm_system: str = ""

    # Description for logging
    description: str = ""


def parse_blueprint_node(step: dict[str, Any]) -> WorkflowNode:
    """
    Parse a single blueprint step dict into a typed WorkflowNode.

    Accepts both LLM blueprint format and MicroTask.model_dump() format:
      - LLM format:      id, type, artifact, args
      - MicroTask format: task_id, node_type, output_artifact, inputs, node_config

    Infers node_type from the step's fields if not explicitly set.

    Args:
        step: Raw blueprint step from the planner (either format)

    Returns:
        WorkflowNode with appropriate type and fields
    """
    # Merge node_config into a lookup dict so advanced fields are accessible
    # at the top level.  MicroTask stores loop_over, condition, etc. inside
    # node_config rather than at the step root.
    merged = {**step.get("node_config", {}), **step}

    # Node type: accept "type" (LLM) or "node_type" (MicroTask)
    node_type_str = merged.get("type", "") or merged.get("node_type", "")

    # Auto-detect node type from fields if not explicit
    if not node_type_str:
        if "loop_over" in merged or "loop_body" in merged:
            node_type_str = "loop"
        elif "condition" in merged:
            node_type_str = "switch"
        elif "merge_inputs" in merged or "merge_strategy" in merged:
            node_type_str = "merge"
        elif "goal" in merged:
            node_type_str = "agentic"
        elif "llm_prompt" in merged:
            node_type_str = "llm"
        elif merged.get("tool", "") in ("execute_code", "run_python"):
            node_type_str = "code"
        else:
            node_type_str = "tool"

    try:
        node_type = NodeType(node_type_str)
    except ValueError:
        logger.warning(f"Unknown node type '{node_type_str}', defaulting to tool")
        node_type = NodeType.TOOL

    # ID: accept "id" (LLM) or "task_id" (MicroTask)
    node_id = merged.get("id") or merged.get("task_id", f"node_{id(step)}")

    # Args: accept "args" (LLM) or "inputs" (MicroTask)
    # Use explicit None check — an empty {} is a valid args dict and should
    # NOT fall through to "inputs".
    args = merged.get("args")
    if args is None:
        args = merged.get("inputs")
    if not isinstance(args, dict):
        args = {}

    # Output artifact: accept "artifact" (LLM) or "output_artifact" (MicroTask)
    output_artifact = merged.get("artifact") or merged.get("output_artifact")

    # Phase: accept int or str, normalise to int for WorkflowNode
    raw_phase = merged.get("phase", 1)
    try:
        phase = int(raw_phase)
    except (ValueError, TypeError):
        phase = 1

    # For merge_inputs, avoid accidentally using "inputs" (MicroTask dict field)
    merge_inputs_raw = merged.get("merge_inputs")
    if merge_inputs_raw is None:
        # Only fall back to "inputs" if it's a list (merge semantic), not a dict
        inputs_field = merged.get("inputs")
        merge_inputs_raw = inputs_field if isinstance(inputs_field, list) else []
    if not isinstance(merge_inputs_raw, list):
        merge_inputs_raw = []

    node = WorkflowNode(
        id=node_id,
        node_type=node_type,
        phase=phase,
        tool=merged.get("tool", ""),
        args=args,
        input_mapping=merged.get("input_mapping", {}),
        output_artifact=output_artifact,
        depends_on=merged.get("depends_on", []),
        description=merged.get("description", ""),
        # SwitchNode
        condition=merged.get("condition", ""),
        true_branch=merged.get("true_branch", merged.get("true", [])),
        false_branch=merged.get("false_branch", merged.get("false", [])),
        # LoopNode
        loop_over=merged.get("loop_over", merged.get("over", "")),
        loop_body=merged.get("loop_body", merged.get("body", [])),
        max_parallel=merged.get("max_parallel", 10),
        loop_variable=merged.get("loop_variable", "item"),
        # MergeNode
        merge_inputs=merge_inputs_raw,
        merge_strategy=merged.get("merge_strategy", "concat"),
        # AgenticNode
        goal=merged.get("goal", ""),
        agent_max_steps=merged.get("agent_max_steps", merged.get("max_steps", 8)),
        agent_tools=merged.get("agent_tools", merged.get("tools", [])),
        # LLMNode
        llm_prompt=merged.get("llm_prompt", merged.get("prompt", "")),
        llm_system=merged.get("llm_system", merged.get("system", "")),
    )

    return node


def parse_blueprint(blueprint_steps: list[dict[str, Any]]) -> list[WorkflowNode]:
    """
    Parse a full blueprint into a list of WorkflowNodes.

    Also infers dependencies from phase numbers if not explicitly set.

    Args:
        blueprint_steps: List of raw blueprint step dicts

    Returns:
        List of WorkflowNode instances with resolved dependencies
    """
    nodes = [parse_blueprint_node(step) for step in blueprint_steps]

    # Build phase map for dependency inference
    phase_map: dict[int, list[str]] = {}
    for node in nodes:
        if node.phase not in phase_map:
            phase_map[node.phase] = []
        phase_map[node.phase].append(node.id)

    sorted_phases = sorted(phase_map.keys())

    # Infer dependencies from phases if not explicitly set
    for node in nodes:
        if not node.depends_on:
            phase_idx = sorted_phases.index(node.phase)
            if phase_idx > 0:
                prev_phase = sorted_phases[phase_idx - 1]
                node.depends_on = phase_map.get(prev_phase, [])

    return nodes
