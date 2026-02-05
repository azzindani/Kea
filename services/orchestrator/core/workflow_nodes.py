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

    Infers node_type from the step's fields if not explicitly set.

    Args:
        step: Raw blueprint step from the planner

    Returns:
        WorkflowNode with appropriate type and fields
    """
    node_type_str = step.get("type", "")

    # Auto-detect node type from fields if not explicit
    if not node_type_str:
        if "loop_over" in step or "loop_body" in step:
            node_type_str = "loop"
        elif "condition" in step:
            node_type_str = "switch"
        elif "merge_inputs" in step or "merge_strategy" in step:
            node_type_str = "merge"
        elif "goal" in step:
            node_type_str = "agentic"
        elif "llm_prompt" in step:
            node_type_str = "llm"
        elif step.get("tool", "") in ("execute_code", "run_python"):
            node_type_str = "code"
        else:
            node_type_str = "tool"

    try:
        node_type = NodeType(node_type_str)
    except ValueError:
        logger.warning(f"Unknown node type '{node_type_str}', defaulting to tool")
        node_type = NodeType.TOOL

    node = WorkflowNode(
        id=step.get("id", f"node_{id(step)}"),
        node_type=node_type,
        phase=step.get("phase", 1),
        tool=step.get("tool", ""),
        args=step.get("args", {}),
        input_mapping=step.get("input_mapping", {}),
        output_artifact=step.get("artifact"),
        depends_on=step.get("depends_on", []),
        description=step.get("description", ""),
        # SwitchNode
        condition=step.get("condition", ""),
        true_branch=step.get("true_branch", step.get("true", [])),
        false_branch=step.get("false_branch", step.get("false", [])),
        # LoopNode
        loop_over=step.get("loop_over", step.get("over", "")),
        loop_body=step.get("loop_body", step.get("body", [])),
        max_parallel=step.get("max_parallel", 10),
        loop_variable=step.get("loop_variable", "item"),
        # MergeNode
        merge_inputs=step.get("merge_inputs", step.get("inputs", [])),
        merge_strategy=step.get("merge_strategy", "concat"),
        # AgenticNode
        goal=step.get("goal", ""),
        agent_max_steps=step.get("agent_max_steps", step.get("max_steps", 8)),
        agent_tools=step.get("agent_tools", step.get("tools", [])),
        # LLMNode
        llm_prompt=step.get("llm_prompt", step.get("prompt", "")),
        llm_system=step.get("llm_system", step.get("system", "")),
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
