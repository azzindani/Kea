"""
Task-Level DAG Executor.

Replaces the phase-based execution loop with true dependency-driven execution.
Tasks fire as soon as their specific dependencies are satisfied, not when
their entire phase completes.

Key Features:
- Individual task dependency tracking (not phase-level)
- Streaming artifact publication (downstream unblocks immediately)
- Support for all WorkflowNode types (tool, code, llm, switch, loop, merge, agentic)
- Integrated microplanner checkpoints for reactive replanning
- Configurable concurrency via semaphore
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Awaitable

from shared.logging import get_logger
from services.orchestrator.core.assembler import ArtifactStore, resolve_inputs, resolve_and_wire_inputs
from services.orchestrator.core.workflow_nodes import (
    WorkflowNode, NodeType, NodeStatus, NodeResult,
    parse_blueprint_node,
)

logger = get_logger(__name__)


@dataclass
class DAGExecutionResult:
    """Result from a full DAG execution."""
    total_nodes: int = 0
    completed: int = 0
    failed: int = 0
    skipped: int = 0
    node_results: dict[str, NodeResult] = field(default_factory=dict)
    artifacts_produced: dict[str, Any] = field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    replans_triggered: int = 0

    @property
    def success_rate(self) -> float:
        if self.total_nodes == 0:
            return 0.0
        return self.completed / self.total_nodes


# Type alias for the function that executes a single node
NodeExecutor = Callable[[WorkflowNode, dict[str, Any]], Awaitable[NodeResult]]

# Type alias for the microplanner callback
MicroplannerCallback = Callable[
    [WorkflowNode, NodeResult, list[WorkflowNode], ArtifactStore],
    Awaitable[list[WorkflowNode] | None]
]


class DAGExecutor:
    """
    Execute a DAG of WorkflowNodes with true dependency-level parallelism.

    Instead of grouping by phase and waiting for each phase to complete,
    this executor tracks individual task dependencies and fires tasks
    as soon as their inputs are ready.

    Example:
        executor = DAGExecutor(
            store=artifact_store,
            node_executor=my_tool_runner,
            max_parallel=8,
        )
        result = await executor.execute(nodes)
    """

    def __init__(
        self,
        store: ArtifactStore,
        node_executor: NodeExecutor,
        max_parallel: int = 6,
        microplanner: MicroplannerCallback | None = None,
    ):
        self.store = store
        self.node_executor = node_executor
        self.max_parallel = max_parallel
        self.microplanner = microplanner

        # Internal state
        self._nodes: dict[str, WorkflowNode] = {}
        self._completed: set[str] = set()
        self._failed: set[str] = set()
        self._running: set[str] = set()
        self._semaphore: asyncio.Semaphore | None = None
        self._result = DAGExecutionResult()

    async def execute(self, nodes: list[WorkflowNode]) -> DAGExecutionResult:
        """
        Execute the full DAG.

        Nodes fire as soon as all their dependencies are satisfied.
        New nodes can be injected mid-execution by the microplanner.

        Args:
            nodes: List of WorkflowNodes to execute

        Returns:
            DAGExecutionResult with all outcomes
        """
        self._result = DAGExecutionResult(
            total_nodes=len(nodes),
            started_at=datetime.utcnow(),
        )
        self._nodes = {n.id: n for n in nodes}
        self._completed = set()
        self._failed = set()
        self._running = set()
        self._semaphore = asyncio.Semaphore(self.max_parallel)

        logger.info(
            f"🚀 DAG Executor starting: {len(nodes)} nodes, "
            f"max_parallel={self.max_parallel}"
        )

        # Main execution loop
        while True:
            ready = self._get_ready_nodes()

            if not ready and not self._running:
                # Nothing ready and nothing running — we're done
                break

            if not ready:
                # Nothing ready but tasks are running — wait for one to complete
                await asyncio.sleep(0.05)
                continue

            # Launch all ready nodes concurrently (up to semaphore limit)
            tasks = []
            for node in ready:
                node.status = NodeStatus.RUNNING
                self._running.add(node.id)
                tasks.append(self._execute_node(node))

            # Don't await all — let them run and check for new ready nodes
            for coro in asyncio.as_completed(tasks):
                await coro
                # After each completion, loop will re-check ready nodes
                # This is the "streaming" behavior — don't wait for all

        self._result.completed_at = datetime.utcnow()

        # Count skipped nodes (dependencies never satisfied)
        for node_id, node in self._nodes.items():
            if node_id not in self._completed and node_id not in self._failed:
                node.status = NodeStatus.SKIPPED
                self._result.skipped += 1

        logger.info(
            f"✅ DAG complete: {self._result.completed} ok, "
            f"{self._result.failed} failed, {self._result.skipped} skipped, "
            f"{self._result.replans_triggered} replans"
        )

        return self._result

    def _get_ready_nodes(self) -> list[WorkflowNode]:
        """Find nodes whose dependencies are all satisfied."""
        ready = []
        for node_id, node in self._nodes.items():
            if node.status != NodeStatus.PENDING:
                continue

            # Check all dependencies are completed
            deps_met = all(
                dep_id in self._completed
                for dep_id in node.depends_on
            )

            # Check none of the dependencies failed (unless we want partial execution)
            deps_failed = any(
                dep_id in self._failed
                for dep_id in node.depends_on
            )

            if deps_met and not deps_failed:
                ready.append(node)
            elif deps_failed:
                # Dependency failed — mark this node as failed too
                node.status = NodeStatus.FAILED
                self._failed.add(node_id)
                self._result.failed += 1
                self._result.node_results[node_id] = NodeResult(
                    node_id=node_id,
                    status=NodeStatus.FAILED,
                    error="Upstream dependency failed",
                )
                logger.warning(f"⚠️ Node {node_id} skipped: upstream dependency failed")

        return ready

    async def _execute_node(self, node: WorkflowNode) -> None:
        """Execute a single node with semaphore control."""
        async with self._semaphore:
            try:
                # ARTIFACT REUSE: Check if we have a cached result for this exact task
                # This prevents re-running successful tools on retry
                cached_result = self._check_artifact_cache(node)
                if cached_result:
                    logger.info(f"♻️ Reusing cached artifact for {node.id} (skipping execution)")
                    result = cached_result
                else:
                    # Execute normally
                    result = await self._dispatch_node(node)

                node.result = result
                node.status = result.status

                if result.status == NodeStatus.COMPLETED:
                    self._completed.add(node.id)
                    self._result.completed += 1
                    self._result.node_results[node.id] = result

                    # Store artifacts with both node.id and cache key
                    if node.output_artifact and result.artifacts:
                        for key, value in result.artifacts.items():
                            self.store.store(node.id, key, value)
                            # Also store with cache key for reuse
                            cache_key = self._get_artifact_cache_key(node)
                            self.store.store(cache_key, key, value)
                    elif node.output_artifact and result.output is not None:
                        self.store.store(node.id, node.output_artifact, result.output)
                        # Also store with cache key for reuse
                        cache_key = self._get_artifact_cache_key(node)
                        self.store.store(cache_key, node.output_artifact, result.output)

                    # Register any children spawned (from loop/switch nodes)
                    for child_id in result.children_spawned:
                        if child_id in self._nodes:
                            self._result.total_nodes += 1

                    # Microplanner checkpoint
                    if self.microplanner:
                        remaining = [
                            n for n in self._nodes.values()
                            if n.status == NodeStatus.PENDING
                        ]
                        new_nodes = await self.microplanner(
                            node, result, remaining, self.store
                        )
                        if new_nodes:
                            self._inject_nodes(new_nodes)

                else:
                    self._failed.add(node.id)
                    self._result.failed += 1
                    self._result.node_results[node.id] = result
                    logger.warning(f"❌ Node {node.id} failed: {result.error}")

            except Exception as e:
                node.status = NodeStatus.FAILED
                self._failed.add(node.id)
                self._result.failed += 1
                self._result.node_results[node.id] = NodeResult(
                    node_id=node.id,
                    status=NodeStatus.FAILED,
                    error=str(e),
                )
                logger.error(f"❌ Node {node.id} exception: {e}")

            finally:
                self._running.discard(node.id)

    def _get_artifact_cache_key(self, node: WorkflowNode) -> str:
        """Generate deterministic cache key from tool + args for artifact reuse."""
        import hashlib
        import json

        # Create deterministic key from tool name + args
        key_data = {
            'tool': node.tool,
            'args': node.args
        }
        key_str = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()[:8]

        return f"cache_{node.tool}_{key_hash}"

    def _check_artifact_cache(self, node: WorkflowNode) -> NodeResult | None:
        """Check if we have a cached artifact for this exact task."""
        cache_key = self._get_artifact_cache_key(node)

        # Check if artifact exists in store
        if node.output_artifact:
            cached_value = self.store.get(cache_key, node.output_artifact)
            if cached_value is not None:
                # Return a NodeResult with cached data
                return NodeResult(
                    node_id=node.id,
                    status=NodeStatus.COMPLETED,
                    output=cached_value,
                    artifacts={node.output_artifact: cached_value},
                    metadata={'cached': True, 'cache_key': cache_key}
                )

        return None

    async def _dispatch_node(self, node: WorkflowNode) -> NodeResult:
        """Dispatch execution based on node type."""
        # Resolve input mappings
        # Resolve input mappings AND Auto-Wire
        # Replaces: if node.input_mapping: resolved = resolve_inputs(...)
        resolved = await resolve_and_wire_inputs(
            input_mapping=node.input_mapping,
            current_args=node.args,
            tool_name=node.tool,
            store=self.store
        )
        node.args.update(resolved)

        if node.node_type == NodeType.LOOP:
            return await self._execute_loop(node)
        elif node.node_type == NodeType.SWITCH:
            return await self._execute_switch(node)
        elif node.node_type == NodeType.MERGE:
            return await self._execute_merge(node)
        else:
            # TOOL, CODE, LLM, AGENTIC — all go through node_executor
            return await self.node_executor(node, node.args)

    async def _execute_loop(self, node: WorkflowNode) -> NodeResult:
        """
        Execute a LoopNode: iterate over a list artifact and spawn
        sub-tasks for each item.
        """
        # Resolve the collection to iterate over
        loop_data = None
        if node.loop_over:
            from services.orchestrator.core.assembler import _resolve_jsonpath
            loop_data = _resolve_jsonpath(node.loop_over, self.store)

        if loop_data is None:
            # Try as direct artifact reference
            loop_data = self.store.get(node.loop_over)

        if not isinstance(loop_data, (list, tuple)):
            # Try to parse as string list
            if isinstance(loop_data, str):
                loop_data = [item.strip() for item in loop_data.split(",") if item.strip()]
            else:
                return NodeResult(
                    node_id=node.id,
                    status=NodeStatus.FAILED,
                    error=f"Loop target '{node.loop_over}' is not iterable: {type(loop_data)}",
                )

        logger.info(
            f"🔄 Loop node {node.id}: iterating over {len(loop_data)} items "
            f"(max_parallel={node.max_parallel})"
        )

        # Spawn child nodes for each item
        children: list[WorkflowNode] = []
        for i, item in enumerate(loop_data):
            for body_step in node.loop_body:
                child_step = dict(body_step)  # Copy
                child_id = f"{node.id}_iter{i}_{child_step.get('id', str(i))}"
                child_step["id"] = child_id
                child_step["phase"] = node.phase  # Same phase
                child_step["depends_on"] = []  # Independent within loop

                # Inject the loop variable into args
                child_args = child_step.get("args", {})
                # Replace {{item}} placeholders with actual value
                child_args = _substitute_loop_var(
                    child_args, node.loop_variable, item
                )
                child_step["args"] = child_args

                # Also substitute in input_mapping
                if "input_mapping" in child_step:
                    child_step["input_mapping"] = _substitute_loop_var(
                        child_step["input_mapping"], node.loop_variable, item
                    )

                child_node = parse_blueprint_node(child_step)
                children.append(child_node)

        # Execute children with bounded parallelism
        sem = asyncio.Semaphore(node.max_parallel)
        child_results: list[NodeResult] = []

        async def run_child(child: WorkflowNode) -> NodeResult:
            async with sem:
                # Use Auto-Wiring for loop children too
                resolved = await resolve_and_wire_inputs(
                    input_mapping=child.input_mapping,
                    current_args=child.args,
                    tool_name=child.tool,
                    store=self.store
                )
                child.args.update(resolved)
                return await self.node_executor(child, child.args)

        tasks = [run_child(c) for c in children]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results
        all_outputs = []
        for i, res in enumerate(results):
            if isinstance(res, NodeResult):
                child_results.append(res)
                if res.status == NodeStatus.COMPLETED and res.output is not None:
                    all_outputs.append(res.output)
                # Store child artifacts
                if isinstance(res, NodeResult) and res.artifacts:
                    for key, val in res.artifacts.items():
                        self.store.store(children[i].id, key, val)
            elif isinstance(res, Exception):
                child_results.append(NodeResult(
                    node_id=children[i].id,
                    status=NodeStatus.FAILED,
                    error=str(res),
                ))

        completed_count = sum(
            1 for r in child_results if r.status == NodeStatus.COMPLETED
        )

        logger.info(
            f"🔄 Loop {node.id} complete: {completed_count}/{len(children)} succeeded"
        )

        return NodeResult(
            node_id=node.id,
            status=NodeStatus.COMPLETED,
            output=all_outputs,
            artifacts={node.output_artifact: all_outputs} if node.output_artifact else {},
            children_spawned=[c.id for c in children],
            metadata={
                "total_iterations": len(loop_data),
                "children_completed": completed_count,
                "children_failed": len(children) - completed_count,
            },
        )

    async def _execute_switch(self, node: WorkflowNode) -> NodeResult:
        """
        Execute a SwitchNode: evaluate condition and inject the
        appropriate branch into the DAG.
        """
        condition_result = _evaluate_condition(node.condition, self.store)

        logger.info(
            f"🔀 Switch node {node.id}: condition='{node.condition}' "
            f"→ {'TRUE' if condition_result else 'FALSE'}"
        )

        branch = node.true_branch if condition_result else node.false_branch
        branch_name = "true" if condition_result else "false"

        # Convert branch steps to nodes and inject them
        children: list[WorkflowNode] = []
        for step in branch:
            child_step = dict(step)
            child_id = f"{node.id}_{branch_name}_{child_step.get('id', str(len(children)))}"
            child_step["id"] = child_id
            child_step["depends_on"] = [node.id]
            child_node = parse_blueprint_node(child_step)
            children.append(child_node)

        # Inject children into the live DAG
        self._inject_nodes(children)

        return NodeResult(
            node_id=node.id,
            status=NodeStatus.COMPLETED,
            output=condition_result,
            artifacts={node.output_artifact: condition_result} if node.output_artifact else {},
            children_spawned=[c.id for c in children],
            metadata={"branch_taken": branch_name},
        )

    async def _execute_merge(self, node: WorkflowNode) -> NodeResult:
        """
        Execute a MergeNode: collect outputs from all merge_inputs
        and combine them.
        """
        collected = {}
        for input_id in node.merge_inputs:
            if input_id in self._result.node_results:
                res = self._result.node_results[input_id]
                collected[input_id] = res.output
            else:
                # Try artifact store
                artifacts = self.store.list_artifacts(input_id)
                if artifacts.get(input_id):
                    collected[input_id] = artifacts[input_id]

        # Apply merge strategy
        if node.merge_strategy == "concat":
            if all(isinstance(v, list) for v in collected.values()):
                merged = []
                for v in collected.values():
                    merged.extend(v)
            elif all(isinstance(v, str) for v in collected.values()):
                merged = "\n\n".join(collected.values())
            else:
                merged = list(collected.values())
        elif node.merge_strategy == "dict":
            merged = collected
        elif node.merge_strategy == "first":
            merged = next(iter(collected.values()), None)
        else:
            merged = collected

        logger.info(
            f"🔗 Merge node {node.id}: merged {len(collected)} inputs "
            f"(strategy={node.merge_strategy})"
        )

        return NodeResult(
            node_id=node.id,
            status=NodeStatus.COMPLETED,
            output=merged,
            artifacts={node.output_artifact: merged} if node.output_artifact else {},
        )

    def _inject_nodes(self, new_nodes: list[WorkflowNode]) -> None:
        """Inject new nodes into the live DAG during execution."""
        for node in new_nodes:
            if node.id not in self._nodes:
                self._nodes[node.id] = node
                self._result.total_nodes += 1
                self._result.replans_triggered += 1
                logger.info(f"➕ Injected node: {node.id} ({node.node_type.value})")


# ============================================================================
# Helper Functions
# ============================================================================

def _substitute_loop_var(obj: Any, var_name: str, value: Any) -> Any:
    """Recursively substitute {{var_name}} in strings within a dict/list."""
    placeholder = f"{{{{{var_name}}}}}"

    if isinstance(obj, str):
        if obj == placeholder:
            return value  # Preserve type
        return obj.replace(placeholder, str(value))
    elif isinstance(obj, dict):
        return {k: _substitute_loop_var(v, var_name, value) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_substitute_loop_var(item, var_name, value) for item in obj]
    return obj


def _evaluate_condition(condition: str, store: ArtifactStore) -> bool:
    """
    Evaluate a condition expression against the artifact store.

    Supports simple expressions like:
    - "len({{s1.artifacts.data}}) > 10"
    - "{{s1.artifacts.status}} == 'success'"
    - "{{s1.artifacts.count}} >= 5"
    """
    from services.orchestrator.core.assembler import PLACEHOLDER_PATTERN, _resolve_jsonpath

    # Resolve all placeholders in the condition
    resolved_condition = condition
    matches = PLACEHOLDER_PATTERN.findall(condition)
    for match in matches:
        value = _resolve_jsonpath(match, store)
        if value is None:
            value = store.get(match)
        if value is not None:
            placeholder = f"{{{{{match}}}}}"
            resolved_condition = resolved_condition.replace(placeholder, repr(value))
        else:
            logger.warning(f"⚠️ Switch condition: unresolved placeholder '{match}'")
            return False

    # Evaluate safely (restricted builtins)
    try:
        safe_builtins = {"len": len, "int": int, "float": float, "str": str, "bool": bool}
        result = eval(resolved_condition, {"__builtins__": safe_builtins})
        return bool(result)
    except Exception as e:
        logger.warning(f"⚠️ Switch condition eval failed: '{resolved_condition}' → {e}")
        return False
