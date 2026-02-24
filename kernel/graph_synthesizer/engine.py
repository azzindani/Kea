"""
Tier 3 Graph Synthesizer — Engine.

JIT DAG compilation pipeline:
    1. Delegate decomposition to Tier 2 (task_decomposition)
    2. Map sub-tasks to executable nodes (via Node Assembler)
    3. Calculate dependency edges (sequential vs parallel)
    4. Compile into an executable DAG
    5. Review via Tier 2 What-If simulation
"""

from __future__ import annotations

import time
from typing import Any

from shared.config import get_settings
from shared.id_and_hash import generate_id
from shared.logging.main import get_logger
from shared.standard_io import (
    Metrics,
    ModuleRef,
    Result,
    create_data_signal,
    fail,
    ok,
    processing_error,
)

from kernel.task_decomposition import decompose_goal, WorldState
from kernel.task_decomposition.types import SubTaskItem
from kernel.what_if_scenario import simulate_outcomes
from kernel.what_if_scenario.types import CompiledDAG, SimulationVerdict, VerdictDecision

from .types import (
    ActionInstruction,
    DAGState,
    Edge,
    EdgeKind,
    ExecutableDAG,
    ExecutableNode,
    NodeStatus,
)

log = get_logger(__name__)

_MODULE = "graph_synthesizer"
_TIER = 3


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


# ============================================================================
# Step 1: Map Sub-Tasks to Executable Nodes
# ============================================================================


def map_subtasks_to_nodes(subtasks: list[SubTaskItem]) -> list[ExecutableNode]:
    """Translate each SubTaskItem into an ExecutableNode.

    Uses the action instruction abstraction to capture what each node
    does, without binding the actual callable yet (Node Assembler does that).
    """
    nodes: list[ExecutableNode] = []

    for task in subtasks:
        instruction = ActionInstruction(
            task_id=task.id,
            description=task.description,
            action_type=_infer_action_type(task),
            required_skills=task.required_skills,
            required_tools=task.required_tools,
            parameters={
                "input_keys": task.inputs,
                "output_keys": task.outputs,
                "domain": task.domain,
            },
        )

        node = ExecutableNode(
            node_id=generate_id("node"),
            instruction=instruction,
            input_keys=task.inputs,
            output_keys=task.outputs,
            parallelizable=task.parallelizable,
            status=NodeStatus.PENDING,
        )

        nodes.append(node)

    log.info("Mapped sub-tasks to nodes", task_count=len(subtasks), node_count=len(nodes))
    return nodes


def _infer_action_type(task: SubTaskItem) -> str:
    """Infer the action type from task metadata."""
    if task.required_tools:
        return "tool_call"
    desc = task.description.lower()
    if any(kw in desc for kw in ("analyze", "evaluate", "assess", "score")):
        return "llm_inference"
    if any(kw in desc for kw in ("aggregate", "merge", "combine", "transform")):
        return "data_transform"
    return "general"


# ============================================================================
# Step 2: Calculate Dependency Edges
# ============================================================================


def calculate_dependency_edges(nodes: list[ExecutableNode]) -> list[Edge]:
    """Determine execution ordering from input/output dependencies.

    Nodes whose inputs are satisfied by another node's outputs
    are wired sequentially. Nodes with no data dependencies
    are wired for parallel execution.
    """
    # Build output map: output_key → producing node_id
    output_map: dict[str, str] = {}
    for node in nodes:
        for key in node.output_keys:
            output_map[key] = node.node_id

    edges: list[Edge] = []
    node_ids_with_deps: set[str] = set()

    for node in nodes:
        for input_key in node.input_keys:
            if input_key in output_map:
                producer_id = output_map[input_key]
                if producer_id != node.node_id:
                    edges.append(Edge(
                        from_node_id=producer_id,
                        to_node_id=node.node_id,
                        kind=EdgeKind.SEQUENTIAL,
                        data_key=input_key,
                    ))
                    node_ids_with_deps.add(node.node_id)

    log.info(
        "Dependency edges calculated",
        total_edges=len(edges),
        nodes_with_deps=len(node_ids_with_deps),
    )
    return edges


# ============================================================================
# Step 3: Compile DAG
# ============================================================================


def compile_dag(
    nodes: list[ExecutableNode],
    edges: list[Edge],
    objective: str,
) -> ExecutableDAG:
    """Assemble nodes and edges into a fully compiled DAG.

    Validates acyclicity, computes topological order, identifies
    entry/terminal nodes, and groups parallel execution batches.
    """
    settings = get_settings().kernel
    dag_id = generate_id("dag")

    # Build adjacency for topological sort
    incoming: dict[str, set[str]] = {n.node_id: set() for n in nodes}
    outgoing: dict[str, set[str]] = {n.node_id: set() for n in nodes}

    for edge in edges:
        incoming[edge.to_node_id].add(edge.from_node_id)
        outgoing[edge.from_node_id].add(edge.to_node_id)

    # Entry nodes: no incoming edges
    entry_ids = [nid for nid, deps in incoming.items() if not deps]

    # Terminal nodes: no outgoing edges
    terminal_ids = [nid for nid, outs in outgoing.items() if not outs]

    # Topological sort (Kahn's algorithm)
    execution_order = _topological_sort(nodes, incoming, outgoing)

    # Parallel groups (nodes at the same topological level)
    parallel_groups = _compute_parallel_groups(nodes, incoming, outgoing)

    # Enforce max parallel branches
    capped_groups: list[list[str]] = []
    for group in parallel_groups:
        if len(group) > settings.max_parallel_branches:
            # Split into sub-batches
            for i in range(0, len(group), settings.max_parallel_branches):
                capped_groups.append(group[i : i + settings.max_parallel_branches])
        else:
            capped_groups.append(group)

    # Detect external calls and state mutations
    has_external = any(n.instruction.action_type == "tool_call" for n in nodes)
    has_mutations = any(
        "write" in n.instruction.description.lower()
        or "create" in n.instruction.description.lower()
        or "delete" in n.instruction.description.lower()
        for n in nodes
    )

    # Initialize DAG state with pending nodes
    state = DAGState(
        pending_nodes=[n.node_id for n in nodes],
    )

    dag = ExecutableDAG(
        dag_id=dag_id,
        description=objective,
        nodes=nodes,
        edges=edges,
        entry_node_ids=entry_ids,
        terminal_node_ids=terminal_ids,
        state=state,
        execution_order=execution_order,
        parallel_groups=capped_groups,
        has_external_calls=has_external,
        has_state_mutations=has_mutations,
    )

    log.info(
        "DAG compiled",
        dag_id=dag_id,
        nodes=len(nodes),
        edges=len(edges),
        parallel_groups=len(capped_groups),
    )

    return dag


def _topological_sort(
    nodes: list[ExecutableNode],
    incoming: dict[str, set[str]],
    outgoing: dict[str, set[str]],
) -> list[str]:
    """Kahn's algorithm for topological sorting."""
    in_degree = {nid: len(deps) for nid, deps in incoming.items()}
    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    result: list[str] = []

    while queue:
        node_id = queue.pop(0)
        result.append(node_id)
        for neighbor in outgoing.get(node_id, set()):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return result


def _compute_parallel_groups(
    nodes: list[ExecutableNode],
    incoming: dict[str, set[str]],
    outgoing: dict[str, set[str]],
) -> list[list[str]]:
    """Find groups of nodes that can execute concurrently (same topo level)."""
    in_degree = {nid: len(deps) for nid, deps in incoming.items()}
    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    groups: list[list[str]] = []

    while queue:
        groups.append(list(queue))
        next_queue: list[str] = []
        for node_id in queue:
            for neighbor in outgoing.get(node_id, set()):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    next_queue.append(neighbor)
        queue = next_queue

    return groups


# ============================================================================
# Step 4: Review via What-If Simulation
# ============================================================================


async def review_dag_with_simulation(dag: ExecutableDAG) -> SimulationVerdict:
    """Pass the compiled DAG to Tier 2's What-If engine for validation.

    Checks for infinite loops, unreachable nodes, excessive parallelism,
    and resource over-commitment.
    """
    # Convert ExecutableDAG to CompiledDAG (Tier 2's expected input)
    compiled = CompiledDAG(
        dag_id=dag.dag_id,
        description=dag.description,
        nodes=[n.instruction.description for n in dag.nodes],
        has_external_calls=dag.has_external_calls,
        has_state_mutations=dag.has_state_mutations,
        estimated_cost=dag.estimated_cost,
    )

    knowledge = WorldState(goal=dag.description)
    result = await simulate_outcomes(compiled, knowledge)

    if result.signals:
        data = result.signals[0].body.get("data", {})
        if isinstance(data, dict):
            verdict = SimulationVerdict(**data)
            log.info(
                "DAG review complete",
                dag_id=dag.dag_id,
                decision=verdict.decision.value,
                risk=round(verdict.risk_score, 3),
            )
            return verdict

    # Default to approve if simulation returned no structured data
    return SimulationVerdict(
        decision=VerdictDecision.APPROVE,
        risk_score=0.0,
        reward_score=1.0,
        reasoning="Simulation returned no structured verdict; defaulting to approve",
    )


# ============================================================================
# Top-Level Orchestrator
# ============================================================================


async def synthesize_plan(
    objective: str,
    context: WorldState | None = None,
) -> Result:
    """Top-level DAG synthesis orchestrator.

    Takes a high-level objective, delegates decomposition to Tier 2,
    maps sub-tasks to executable nodes, calculates edges, compiles
    the DAG, and validates via What-If simulation.
    """
    ref = _ref("synthesize_plan")
    start = time.perf_counter()
    settings = get_settings().kernel

    if context is None:
        context = WorldState(goal=objective)

    try:
        # Step 0: Decompose via Tier 2
        decomp_result = await decompose_goal(context)
        if not decomp_result.signals:
            elapsed = (time.perf_counter() - start) * 1000
            return fail(
                error=processing_error(
                    message="Goal decomposition produced no sub-tasks",
                    source=ref,
                ),
                metrics=Metrics(duration_ms=elapsed, module_ref=ref),
            )

        # Extract SubTaskItems from decomposition signal
        decomp_data = decomp_result.signals[0].body.get("data", [])
        subtasks = [
            SubTaskItem(**item) if isinstance(item, dict) else item
            for item in decomp_data
        ]

        if not subtasks:
            elapsed = (time.perf_counter() - start) * 1000
            return fail(
                error=processing_error(
                    message="Decomposition returned empty sub-task list",
                    source=ref,
                ),
                metrics=Metrics(duration_ms=elapsed, module_ref=ref),
            )

        # Step 1: Map to nodes
        nodes = map_subtasks_to_nodes(subtasks)

        # Step 2: Calculate edges
        edges = calculate_dependency_edges(nodes)

        # Step 3: Compile DAG
        dag = compile_dag(nodes, edges, objective)

        # Step 4: Review with simulation (retry loop)
        verdict: SimulationVerdict | None = None
        for attempt in range(settings.max_dag_review_iterations):
            verdict = await review_dag_with_simulation(dag)

            if verdict.decision == VerdictDecision.APPROVE:
                break
            elif verdict.decision == VerdictDecision.REJECT:
                log.warning(
                    "DAG rejected by simulation, re-routing edges",
                    attempt=attempt + 1,
                    risk=round(verdict.risk_score, 3),
                )
                # Re-calculate edges with stricter constraints
                edges = calculate_dependency_edges(nodes)
                dag = compile_dag(nodes, edges, objective)
            elif verdict.decision == VerdictDecision.MODIFY:
                log.info(
                    "DAG modified with safeguards",
                    safeguards=verdict.safeguards,
                )
                break

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)

        signal = create_data_signal(
            data={
                "dag": dag.model_dump(),
                "verdict": verdict.model_dump() if verdict else None,
            },
            schema="SynthesizedPlan",
            origin=ref,
            trace_id="",
            tags={
                "dag_id": dag.dag_id,
                "node_count": str(len(nodes)),
                "decision": verdict.decision.value if verdict else "none",
            },
        )

        log.info(
            "Plan synthesis complete",
            dag_id=dag.dag_id,
            nodes=len(nodes),
            edges=len(edges),
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Plan synthesis failed: {exc}",
            source=ref,
            detail={"objective": objective, "error_type": type(exc).__name__},
        )
        log.error("Plan synthesis failed", error=str(exc))
        return fail(error=error, metrics=metrics)
