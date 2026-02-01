"""
Node Assembler Module.

Core engine for n8n-style node wiring and artifact-based data flow.
Interprets blueprints with input_mapping and manages data passing between nodes.

Key Components:
- ArtifactStore: Job-scoped artifact storage (wraps TaskContextPool)
- NodeAssembler: Wires nodes together, resolves inputs, manages execution
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

from shared.logging import get_logger
from shared.context_pool import TaskContextPool
from shared.mcp.protocol import NodeOutput, ToolResult, TextContent

logger = get_logger(__name__)


# ============================================================================
# Artifact Store
# ============================================================================

class ArtifactStore:
    """
    Job-scoped artifact storage for node outputs.
    
    Wraps TaskContextPool to provide typed artifact access with the
    `{{step_id.artifacts.key}}` convention.
    
    Example:
        store = ArtifactStore(context_pool)
        store.store("fetch_data", "prices_csv", "/vault/bbca.csv")
        path = store.get("fetch_data.artifacts.prices_csv")  # -> "/vault/bbca.csv"
    """
    
    def __init__(self, context_pool: TaskContextPool | None = None):
        self._pool = context_pool
        self._artifacts: dict[str, dict[str, Any]] = defaultdict(dict)
        
    def store(self, step_id: str, key: str, value: Any) -> None:
        """Store an artifact from a completed step."""
        self._artifacts[step_id][key] = value
        
        # Also store in TaskContextPool if available
        if self._pool:
            storage_key = f"{step_id}.artifacts.{key}"
            self._pool.store_data(storage_key, value, f"Artifact from {step_id}")
            
        logger.info(f"📦 Stored artifact: {step_id}.artifacts.{key} = {str(value)[:100]}")
        
    def get(self, reference: str) -> Any | None:
        """
        Get an artifact by reference string.
        
        Args:
            reference: Reference in format "step_id.artifacts.key" or just "step_id.key"
            
        Returns:
            The artifact value, or None if not found
        """
        # Parse reference: "step_id.artifacts.key" or "step_id.key"
        parts = reference.split(".")
        
        if len(parts) >= 3 and parts[1] == "artifacts":
            step_id = parts[0]
            key = ".".join(parts[2:])
        elif len(parts) >= 2:
            step_id = parts[0]
            key = ".".join(parts[1:])
        else:
            logger.warning(f"Invalid artifact reference: {reference}")
            return None
            
        # Try local store first
        if step_id in self._artifacts and key in self._artifacts[step_id]:
            return self._artifacts[step_id][key]
            
        # Try TaskContextPool
        if self._pool:
            return self._pool.get_data(reference)
            
        return None
        
    def list_artifacts(self, step_id: str | None = None) -> dict[str, dict[str, Any]]:
        """List all artifacts, optionally filtered by step_id."""
        if step_id:
            return {step_id: self._artifacts.get(step_id, {})}
        return dict(self._artifacts)
        
    def has_artifact(self, step_id: str, key: str) -> bool:
        """Check if an artifact exists."""
        return step_id in self._artifacts and key in self._artifacts[step_id]


# ============================================================================
# Placeholder Resolution
# ============================================================================

# Pattern for {{step_id.artifacts.key}} placeholders
PLACEHOLDER_PATTERN = re.compile(r"\{\{([^}]+)\}\}")


def resolve_inputs(
    input_mapping: dict[str, str],
    store: ArtifactStore
) -> dict[str, Any]:
    """
    Resolve input_mapping placeholders to actual artifact values.
    
    Args:
        input_mapping: Dict like {"csv_path": "{{fetch_data.artifacts.prices_csv}}"}
        store: ArtifactStore with artifacts from previous steps
        
    Returns:
        Dict with resolved values like {"csv_path": "/vault/bbca.csv"}
        
    Example:
        >>> store.store("fetch_data", "prices_csv", "/vault/bbca.csv")
        >>> resolve_inputs({"csv_path": "{{fetch_data.artifacts.prices_csv}}"}, store)
        {"csv_path": "/vault/bbca.csv"}
    """
    resolved = {}
    
    for key, value in input_mapping.items():
        if isinstance(value, str):
            # Find all placeholders in the value
            matches = PLACEHOLDER_PATTERN.findall(value)
            
            if matches:
                resolved_value = value
                for match in matches:
                    artifact = store.get(match)
                    if artifact is not None:
                        # Replace placeholder with actual value
                        placeholder = f"{{{{{match}}}}}"
                        resolved_value = resolved_value.replace(placeholder, str(artifact))
                        logger.info(f"🔗 Resolved: {key} = {str(artifact)[:100]}")
                    else:
                        logger.warning(f"⚠️ Missing artifact: {match}")
                resolved[key] = resolved_value
            else:
                resolved[key] = value
        else:
            resolved[key] = value
            
    return resolved


# ============================================================================
# Node Assembler
# ============================================================================

@dataclass
class PhaseGroup:
    """Group of tasks that can run in parallel."""
    phase: str | int
    tasks: list[Any]  # List of MicroTask


class NodeAssembler:
    """
    Wires nodes together, resolves inputs, and manages execution.
    
    Responsibilities:
    - Topological sort of tasks based on phases
    - Resolve input_mapping to actual artifact values
    - Execute phases in sequence, tasks in parallel
    - Store artifacts from completed tasks
    
    Example:
        store = ArtifactStore(ctx)
        assembler = NodeAssembler(store)
        
        phases = assembler.topological_sort(micro_tasks)
        for phase_group in phases:
            for task in phase_group.tasks:
                task.inputs.update(assembler.resolve_task_inputs(task))
            results = await execute_parallel(phase_group.tasks)
            for task, result in zip(phase_group.tasks, results):
                assembler.store_task_artifacts(task, result)
    """
    
    def __init__(self, store: ArtifactStore):
        self.store = store
        
    def topological_sort(self, tasks: list[Any]) -> list[PhaseGroup]:
        """
        Group tasks by phase for topological execution order.
        
        Tasks with the same phase run in parallel.
        Phases execute in ascending order.
        
        Args:
            tasks: List of MicroTask objects
            
        Returns:
            List of PhaseGroup, sorted by phase
        """
        phase_map: dict[str | int, list[Any]] = defaultdict(list)
        
        for task in tasks:
            phase = getattr(task, "phase", "1")
            # Convert phase to int if possible for proper sorting
            try:
                phase_key = int(phase)
            except (ValueError, TypeError):
                phase_key = phase
            phase_map[phase_key].append(task)
            
        # Sort by phase (numeric first, then alphabetic)
        sorted_phases = sorted(
            phase_map.keys(),
            key=lambda x: (isinstance(x, str), x)
        )
        
        return [
            PhaseGroup(phase=phase, tasks=phase_map[phase])
            for phase in sorted_phases
        ]
        
    def resolve_task_inputs(self, task: Any) -> dict[str, Any]:
        """
        Resolve a task's input_mapping to actual values.
        
        Args:
            task: MicroTask with input_mapping field
            
        Returns:
            Dict of resolved input values to merge into task.inputs
        """
        input_mapping = getattr(task, "input_mapping", {}) or {}
        if not input_mapping:
            return {}
            
        return resolve_inputs(input_mapping, self.store)
        
    def store_task_artifacts(self, task: Any, result: Any) -> None:
        """
        Store artifacts from a completed task.
        
        Args:
            task: MicroTask with output_artifact field
            result: The result from task execution (ToolResult or NodeOutput)
        """
        output_artifact = getattr(task, "output_artifact", None)
        if not output_artifact:
            return
            
        task_id = getattr(task, "task_id", "unknown")
        
        # Extract value from different result types
        if isinstance(result, NodeOutput):
            # NodeOutput already has artifacts dict
            for key, value in result.artifacts.items():
                self.store.store(task_id, key, value)
        elif isinstance(result, ToolResult):
            # Extract text content as the artifact value
            if result.content:
                for content in result.content:
                    if isinstance(content, TextContent):
                        self.store.store(task_id, output_artifact, content.text)
                        break
        elif isinstance(result, str):
            self.store.store(task_id, output_artifact, result)
        elif isinstance(result, dict):
            # If dict, store the whole thing
            self.store.store(task_id, output_artifact, result)
        else:
            # Fallback: store string representation
            self.store.store(task_id, output_artifact, str(result))
            
    def extract_artifact_from_result(self, result: Any) -> NodeOutput:
        """
        Convert any result type to a standardized NodeOutput.
        
        Args:
            result: Result from tool execution
            
        Returns:
            NodeOutput with extracted artifacts
        """
        if isinstance(result, NodeOutput):
            return result
            
        output = NodeOutput()
        
        if isinstance(result, ToolResult):
            if result.isError:
                output.status = "failed"
                if result.content:
                    output.error = result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
            else:
                output.status = "success"
                # Extract text content as raw_output
                for content in result.content:
                    if isinstance(content, TextContent):
                        text_data = content.text
                        output.artifacts["raw_output"] = text_data
                        
                        # STANDARD I/O: Try to parse ToolOutput JSON
                        # This enables tools to return complex objects (files, data) via text pipe
                        if text_data.strip().startswith("{") and "tool_name" in text_data:
                            try:
                                import json
                                from shared.schemas import ToolOutput
                                
                                # Fast check if it looks like ToolOutput before heavy pydantic parse
                                data = json.loads(text_data)
                                if "tool_name" in data and ("data" in data or "files" in data):
                                    tool_output = ToolOutput(**data)
                                    
                                    # 1. Store structured data
                                    if tool_output.data:
                                        output.artifacts["data"] = tool_output.data.data
                                        
                                    # 2. Store file paths
                                    for file_ref in tool_output.files:
                                        if file_ref.path:
                                            output.artifacts[file_ref.file_id] = file_ref.path
                                            # Also map strictly by file_id for direct access
                                            # e.g. {{step.artifacts.screenshot.png}}
                                            
                                    # 3. Store raw text if different matches
                                    if tool_output.text:
                                        output.artifacts["text"] = tool_output.text
                                        # Update raw_output to be the human readable text, not JSON
                                        output.artifacts["raw_output"] = tool_output.text
                                    
                                    logger.info(f"🧩 Parsed Standard I/O ToolOutput from {tool_output.tool_name}")
                            except Exception as e:
                                # Not a ToolOutput or parse failed - treat as raw text
                                pass
                        
                        break
        elif isinstance(result, str):
            output.artifacts["raw_output"] = result
        elif isinstance(result, dict):
            output.artifacts.update(result)
        else:
            output.artifacts["raw_output"] = str(result)
            
        return output


# ============================================================================
# Convenience Functions
# ============================================================================

def create_assembler(context_pool: TaskContextPool | None = None) -> NodeAssembler:
    """Create a NodeAssembler with the given context pool."""
    store = ArtifactStore(context_pool)
    return NodeAssembler(store)


def resolve_task_inputs_batch(
    tasks: list[Any],
    store: ArtifactStore
) -> list[dict[str, Any]]:
    """
    Resolve inputs for a batch of tasks.
    
    Returns list of resolved input dicts in same order as tasks.
    """
    return [
        resolve_inputs(getattr(task, "input_mapping", {}) or {}, store)
        for task in tasks
    ]


# ============================================================================
# Self-Healing Assembly (Phase 4)
# ============================================================================

@dataclass
class FailureRecord:
    """Record of a task failure for healing purposes."""
    task_id: str
    task: Any  # MicroTask
    error: str
    error_type: str  # "missing_artifact", "tool_error", "timeout", etc.
    timestamp: str = field(default_factory=lambda: __import__("datetime").datetime.now().isoformat())
    patch_attempted: bool = False
    patch_successful: bool = False


@dataclass
class HealingResult:
    """Result of a healing attempt."""
    success: bool
    patch_tasks: list[Any] = field(default_factory=list)  # New tasks to insert
    skip_task: bool = False  # If True, skip the failed task and continue
    escalate: bool = False   # If True, escalate to human/supervisor
    message: str = ""


class SelfHealingAssembler(NodeAssembler):
    """
    NodeAssembler with self-healing capabilities.
    
    Extends NodeAssembler with:
    - execute_with_healing: Execute phases with automatic error recovery
    - _diagnose_failure: Classify failures by type
    - _request_patch: Ask Planner for fix nodes
    - _escalate_to_supervisor: Escalate unrecoverable errors
    
    Example:
        assembler = SelfHealingAssembler(store, supervisor=get_supervisor())
        results = await assembler.execute_with_healing(
            phases,
            execute_fn=execute_tool,
            on_failure=lambda f: logger.error(f"Failed: {f.task_id}")
        )
    """
    
    def __init__(
        self, 
        store: ArtifactStore,
        supervisor: Any = None,
        max_retries: int = 2
    ):
        super().__init__(store)
        self.supervisor = supervisor
        self.max_retries = max_retries
        self.failures: list[FailureRecord] = []
        
    async def execute_with_healing(
        self,
        phases: list[PhaseGroup],
        execute_fn: Callable[[Any], Awaitable[Any]],
        on_failure: Callable[[FailureRecord], None] | None = None
    ) -> list[tuple[Any, Any]]:  # List of (task, result)
        """
        Execute phases with automatic error recovery.
        
        Args:
            phases: List of PhaseGroup from topological_sort
            execute_fn: Async function that executes a single task
            on_failure: Optional callback when a task fails
            
        Returns:
            List of (task, result) tuples for all executed tasks
        """
        all_results: list[tuple[Any, Any]] = []
        
        for phase in phases:
            phase_results = []
            
            for task in phase.tasks:
                # Resolve inputs before execution
                resolved = self.resolve_task_inputs(task)
                if resolved:
                    # Merge resolved inputs into task
                    if hasattr(task, "inputs"):
                        task.inputs.update(resolved)
                    elif hasattr(task, "__dict__"):
                        if "inputs" not in task.__dict__:
                            task.__dict__["inputs"] = {}
                        task.__dict__["inputs"].update(resolved)
                
                # Execute with retry
                result = None
                last_error = None
                
                for attempt in range(self.max_retries + 1):
                    try:
                        result = await execute_fn(task)
                        
                        # Check for error result
                        if isinstance(result, ToolResult) and result.isError:
                            raise Exception(f"Tool error: {result.content[0].text if result.content else 'Unknown'}")
                        
                        # Store artifacts on success
                        self.store_task_artifacts(task, result)
                        break
                        
                    except Exception as e:
                        last_error = str(e)
                        logger.warning(f"⚠️ Task {getattr(task, 'task_id', 'unknown')} attempt {attempt + 1} failed: {e}")
                        
                        if attempt < self.max_retries:
                            # Try to heal
                            healing = await self._attempt_healing(task, str(e))
                            if healing.success:
                                # Execute patch tasks if any
                                for patch_task in healing.patch_tasks:
                                    patch_result = await execute_fn(patch_task)
                                    self.store_task_artifacts(patch_task, patch_result)
                                    phase_results.append((patch_task, patch_result))
                                continue  # Retry original task
                            elif healing.skip_task:
                                logger.info(f"⏭️ Skipping task {getattr(task, 'task_id', 'unknown')}")
                                break
                            elif healing.escalate:
                                await self._escalate_to_supervisor(task, str(e))
                                break
                
                # Record final state
                if result is None and last_error:
                    failure = FailureRecord(
                        task_id=getattr(task, "task_id", "unknown"),
                        task=task,
                        error=last_error,
                        error_type=self._diagnose_failure(last_error)
                    )
                    self.failures.append(failure)
                    if on_failure:
                        on_failure(failure)
                    logger.error(f"❌ Task {failure.task_id} failed permanently: {last_error}")
                else:
                    phase_results.append((task, result))
                    
            all_results.extend(phase_results)
            
        return all_results
    
    def _diagnose_failure(self, error: str) -> str:
        """Classify a failure by its error message."""
        error_lower = error.lower()
        
        if "missing artifact" in error_lower or "not found" in error_lower:
            return "missing_artifact"
        elif "timeout" in error_lower:
            return "timeout"
        elif "rate limit" in error_lower:
            return "rate_limit"
        elif "connection" in error_lower or "network" in error_lower:
            return "network"
        elif "permission" in error_lower or "auth" in error_lower:
            return "auth"
        else:
            return "tool_error"
    
    async def _attempt_healing(self, task: Any, error: str) -> HealingResult:
        """
        Attempt to heal a failed task.
        
        Simple healing strategies:
        - missing_artifact: Log and skip (can't fix without replanning)
        - timeout/rate_limit: Retry (handled by retry loop)
        - network: Retry (handled by retry loop)
        - tool_error: Try fallback tool if available
        """
        error_type = self._diagnose_failure(error)
        task_id = getattr(task, "task_id", "unknown")
        
        logger.info(f"🔧 Attempting healing for {task_id} (error type: {error_type})")
        
        if error_type == "missing_artifact":
            # Can't recover without replanning - skip
            return HealingResult(
                success=False,
                skip_task=True,
                message=f"Missing artifact, skipping task {task_id}"
            )
            
        elif error_type in ("timeout", "rate_limit", "network"):
            # These are transient - retry will handle
            return HealingResult(success=True, message="Transient error, retrying")
            
        elif error_type == "tool_error":
            # Try fallback tools if available
            fallbacks = getattr(task, "fallback_tools", [])
            if fallbacks:
                logger.info(f"🔄 Trying fallback tool for {task_id}: {fallbacks[0]}")
                # Update task to use fallback
                if hasattr(task, "tool"):
                    task.tool = fallbacks[0]
                return HealingResult(success=True, message=f"Switched to fallback: {fallbacks[0]}")
            else:
                # Escalate if no fallbacks
                return HealingResult(
                    success=False,
                    escalate=True,
                    message=f"No fallback tools for {task_id}"
                )
                
        return HealingResult(success=False, skip_task=True, message="Unknown error")
    
    async def _escalate_to_supervisor(self, task: Any, error: str) -> None:
        """Escalate an unrecoverable error to the Supervisor."""
        task_id = getattr(task, "task_id", "unknown")
        
        if self.supervisor:
            try:
                # Try to use Supervisor's escalation
                from services.swarm_manager.core.supervisor import EscalationType
                await self.supervisor.escalate_to_human(
                    escalation_type=EscalationType.ERROR,
                    source="node_assembler",
                    context={
                        "task_id": task_id,
                        "task": task.__dict__ if hasattr(task, "__dict__") else str(task),
                        "error": error
                    },
                    message=f"Task {task_id} failed and could not be healed: {error}"
                )
                logger.info(f"📢 Escalated {task_id} to Supervisor")
            except Exception as e:
                logger.warning(f"Failed to escalate to Supervisor: {e}")
        else:
            logger.warning(f"⚠️ No Supervisor available to escalate {task_id}")
            
    def get_failure_summary(self) -> dict:
        """Get a summary of all failures."""
        return {
            "total": len(self.failures),
            "by_type": {
                error_type: len([f for f in self.failures if f.error_type == error_type])
                for error_type in set(f.error_type for f in self.failures)
            },
            "failures": [
                {"task_id": f.task_id, "error": f.error, "type": f.error_type}
                for f in self.failures
            ]
        }


def create_healing_assembler(
    context_pool: TaskContextPool | None = None,
    supervisor: Any = None
) -> SelfHealingAssembler:
    """Create a SelfHealingAssembler with the given context pool and supervisor."""
    store = ArtifactStore(context_pool)
    return SelfHealingAssembler(store, supervisor=supervisor)

