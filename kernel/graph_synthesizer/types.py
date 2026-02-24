"""
Tier 3 Graph Synthesizer — Types.

Pydantic models for JIT DAG compilation: translating Tier 2 sub-tasks
into executable computational graphs with dependency edges.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ============================================================================
# Edge & Dependency Types
# ============================================================================


class EdgeKind(str, Enum):
    """Classification of dependency edges in the DAG."""

    SEQUENTIAL = "sequential"   # B must wait for A
    PARALLEL = "parallel"       # A and B can run concurrently
    CONDITIONAL = "conditional"  # B runs only if A's output meets condition


class Edge(BaseModel):
    """A directed dependency edge between two nodes in the DAG."""

    from_node_id: str = Field(..., description="Source node ID")
    to_node_id: str = Field(..., description="Target node ID")
    kind: EdgeKind = Field(default=EdgeKind.SEQUENTIAL)
    data_key: str = Field(
        default="",
        description="Name of the data variable flowing along this edge",
    )
    condition: str = Field(
        default="",
        description="Predicate expression for conditional edges",
    )


# ============================================================================
# Executable Node (output of Node Assembler, consumed by Graph Synthesizer)
# ============================================================================


class NodeStatus(str, Enum):
    """Execution status of a DAG node."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ActionInstruction(BaseModel):
    """The core instruction for what a node should do.

    Bridges the gap between Tier 2 sub-task descriptions
    and the executable action callable within a node.
    """

    task_id: str = Field(..., description="Originating SubTaskItem ID")
    description: str = Field(..., description="Human-readable action description")
    action_type: str = Field(
        default="general",
        description="Category of action (e.g., tool_call, llm_inference, data_transform)",
    )
    required_skills: list[str] = Field(default_factory=list)
    required_tools: list[str] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Action-specific configuration parameters",
    )


class ExecutableNode(BaseModel):
    """A fully assembled, executable node in the DAG.

    Each node wraps an action instruction with schema contracts,
    tool bindings, and telemetry hooks injected by the Node Assembler.
    """

    node_id: str = Field(..., description="Unique node identifier")
    instruction: ActionInstruction = Field(..., description="What this node does")
    input_keys: list[str] = Field(
        default_factory=list,
        description="State keys this node reads from",
    )
    output_keys: list[str] = Field(
        default_factory=list,
        description="State keys this node writes to",
    )
    input_schema: str = Field(
        default="dict",
        description="Pydantic model name for input validation",
    )
    output_schema: str = Field(
        default="dict",
        description="Pydantic model name for output validation",
    )
    tool_binding: str | None = Field(
        default=None,
        description="Bound MCP tool identifier (if applicable)",
    )
    parallelizable: bool = Field(
        default=False,
        description="Whether this node can run in parallel with siblings",
    )
    status: NodeStatus = Field(default=NodeStatus.PENDING)


# ============================================================================
# Compiled DAG (Tier 3 output, Tier 4 input)
# ============================================================================


class DAGState(BaseModel):
    """Runtime state container for a compiled DAG.

    Carries the shared state dictionary that nodes read/write,
    plus metadata for progress tracking.
    """

    values: dict[str, Any] = Field(
        default_factory=dict,
        description="Shared key-value state passed between nodes",
    )
    completed_nodes: list[str] = Field(default_factory=list)
    failed_nodes: list[str] = Field(default_factory=list)
    pending_nodes: list[str] = Field(default_factory=list)


class ExecutableDAG(BaseModel):
    """A fully compiled, executable Directed Acyclic Graph.

    This is the primary output of the Graph Synthesizer and the
    primary input to the Tier 4 OODA Loop's Act phase.
    """

    dag_id: str = Field(..., description="Unique DAG identifier")
    description: str = Field(..., description="High-level objective this DAG fulfills")
    nodes: list[ExecutableNode] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    entry_node_ids: list[str] = Field(
        default_factory=list,
        description="Node IDs with no incoming edges (DAG entry points)",
    )
    terminal_node_ids: list[str] = Field(
        default_factory=list,
        description="Node IDs with no outgoing edges (DAG exits)",
    )
    state: DAGState = Field(default_factory=DAGState)
    execution_order: list[str] = Field(
        default_factory=list,
        description="Topologically sorted node ID execution sequence",
    )
    parallel_groups: list[list[str]] = Field(
        default_factory=list,
        description="Groups of node IDs that can execute concurrently",
    )
    has_external_calls: bool = Field(
        default=False,
        description="Whether any node makes external API/tool calls",
    )
    has_state_mutations: bool = Field(
        default=False,
        description="Whether any node modifies persistent state",
    )
    estimated_cost: float = Field(
        default=0.0,
        ge=0.0,
        description="Estimated resource cost for full execution",
    )
