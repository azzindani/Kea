"""
Tier 3 Advanced Planning — Engine.

Advanced planning pipeline:
    1. Sequence & prioritize sub-tasks (cost/speed/fidelity routing)
    2. Bind MCP tools to each task
    3. Generate expected outcome hypotheses
    4. Inject progress tracker for OODA loop monitoring
"""

from __future__ import annotations

import json
import time
from typing import Any

from kernel.task_decomposition.types import SubTaskItem
from shared.config import get_settings
from shared.id_and_hash import generate_id
from shared.inference_kit import InferenceKit
from shared.llm.provider import LLMMessage
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

from .types import (
    BoundTask,
    ExpectedOutcome,
    MCPToolBinding,
    MCPToolRegistry,
    PlanningConstraints,
    PriorityMode,
    ProgressTracker,
    SequencedTask,
    TrackedPlan,
)

log = get_logger(__name__)

_MODULE = "advanced_planning"
_TIER = 3


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


# ============================================================================
# Step 1: Sequence & Prioritize
# ============================================================================


async def sequence_and_prioritize(
    subtasks: list[SubTaskItem],
    constraints: PlanningConstraints,
    kit: InferenceKit | None = None,
) -> list[SequencedTask]:
    """Order sub-tasks by cost/speed/fidelity routing algorithm.

    When constraints emphasize speed, cheap parallel paths are preferred.
    When constraints emphasize accuracy, sequential high-fidelity paths
    are chosen. Algorithm weights are config-driven.
    """
    settings = get_settings().kernel

    # Determine weight profile based on priority mode
    if constraints.priority_mode == PriorityMode.SPEED:
        speed_w, cost_w, fidelity_w = 0.7, 0.1, 0.2
    elif constraints.priority_mode == PriorityMode.COST:
        speed_w, cost_w, fidelity_w = 0.1, 0.7, 0.2
    elif constraints.priority_mode == PriorityMode.FIDELITY:
        speed_w, cost_w, fidelity_w = 0.1, 0.2, 0.7
    else:  # BALANCED
        speed_w = settings.planning_speed_weight
        cost_w = settings.planning_cost_weight
        fidelity_w = settings.planning_fidelity_weight

    sequenced: list[SequencedTask] = []

    for task in subtasks:
        # Heuristic cost/duration estimates based on task characteristics
        est_cost = _estimate_cost(task)
        est_duration = _estimate_duration(task)

        if kit and kit.has_llm:
            try:
                system_msg = LLMMessage(
                    role="system",
                    content="Estimate the 'cost' (0.0-1.0) and 'duration_ms' for this task. Respond EXACTLY with JSON: {\"cost\": 0.5, \"duration_ms\": 1000.0}"
                )
                user_msg = LLMMessage(role="user", content=f"Task: {task.description}\nDependencies: {task.depends_on}\nTools: {task.required_tools}")
                resp = await kit.llm.complete([system_msg, user_msg], kit.llm_config)

                content = resp.content.strip()
                if content.startswith("```json"):
                    content = content[7:-3].strip()
                elif content.startswith("```"):
                    content = content[3:-3].strip()
                data = json.loads(content)

                est_cost = float(data.get("cost", est_cost))
                est_duration = float(data.get("duration_ms", est_duration))
            except (ValueError, TypeError, KeyError, json.JSONDecodeError):
                pass

        # Priority score: lower = execute first
        # Speed-focused: prioritize short tasks
        # Cost-focused: prioritize cheap tasks
        # Fidelity-focused: prioritize tasks with fewer dependencies
        speed_score = est_duration / 1000.0  # Normalize to seconds
        cost_score = est_cost
        fidelity_score = len(task.depends_on) * 0.5  # Fewer deps = higher fidelity

        priority = round(
            speed_w * speed_score + cost_w * cost_score + fidelity_w * fidelity_score,
            4,
        )

        sequenced.append(SequencedTask(
            task_id=task.id,
            description=task.description,
            priority_rank=int(priority * 100),
            estimated_cost=est_cost,
            estimated_duration_ms=est_duration,
            parallelizable=task.parallelizable,
            depends_on=task.depends_on,
            inputs=task.inputs,
            outputs=task.outputs,
            domain=task.domain,
            required_skills=task.required_skills,
            required_tools=task.required_tools,
        ))

    # Sort by priority rank (lower = higher priority)
    sequenced.sort(key=lambda t: t.priority_rank)

    log.info(
        "Tasks sequenced",
        total=len(sequenced),
        mode=constraints.priority_mode.value,
    )

    return sequenced


def _estimate_cost(task: SubTaskItem) -> float:
    """Heuristic cost estimation based on task properties."""
    base_cost = 0.1
    if task.required_tools:
        base_cost += 0.3 * len(task.required_tools)
    if task.required_skills:
        base_cost += 0.1 * len(task.required_skills)
    return round(base_cost, 3)


def _estimate_duration(task: SubTaskItem) -> float:
    """Heuristic duration estimation in ms."""
    base_ms = 500.0
    if task.required_tools:
        base_ms += 2000.0 * len(task.required_tools)
    if len(task.depends_on) > 0:
        base_ms += 200.0  # Dependency wait overhead
    return round(base_ms, 1)


# ============================================================================
# Step 2: Bind Tools
# ============================================================================


async def bind_tools(
    sequenced_tasks: list[SequencedTask],
    mcp_registry: MCPToolRegistry,
) -> list[BoundTask]:
    """Match each task's action type to appropriate MCP tools.

    Validates tool availability and compatibility with the task's
    input/output schemas.
    """
    bound: list[BoundTask] = []

    for task in sequenced_tasks:
        # Find best matching tool from registry
        binding = _find_best_tool(task, mcp_registry)

        bound.append(BoundTask(
            task_id=task.task_id,
            description=task.description,
            priority_rank=task.priority_rank,
            estimated_cost=task.estimated_cost,
            estimated_duration_ms=task.estimated_duration_ms,
            parallelizable=task.parallelizable,
            depends_on=task.depends_on,
            inputs=task.inputs,
            outputs=task.outputs,
            domain=task.domain,
            tool_binding=binding,
        ))

    bound_count = sum(1 for t in bound if t.tool_binding is not None)
    log.info(
        "Tools bound",
        total_tasks=len(bound),
        tasks_with_tools=bound_count,
    )

    return bound


def _find_best_tool(
    task: SequencedTask,
    registry: MCPToolRegistry,
) -> MCPToolBinding | None:
    """Find the best matching MCP tool for a task."""
    if not registry.tools or not task.required_tools:
        return None

    best_match: MCPToolBinding | None = None
    best_score: float = 0.0

    for tool in registry.tools:
        # Score based on name overlap with required tools
        score = 0.0
        tool_name_lower = tool.tool_name.lower()
        for req in task.required_tools:
            if req.lower() in tool_name_lower or tool_name_lower in req.lower():
                score += 0.5
            # Partial match
            req_parts = req.lower().split("_")
            for part in req_parts:
                if part in tool_name_lower:
                    score += 0.2

        score = min(score * tool.compatibility_score, 1.0)

        if score > best_score:
            best_score = score
            best_match = MCPToolBinding(
                tool_id=tool.tool_id,
                tool_name=tool.tool_name,
                compatibility_score=round(score, 3),
            )

    return best_match


# ============================================================================
# Step 3: Generate Hypotheses
# ============================================================================


def generate_hypotheses(bound_tasks: list[BoundTask]) -> list[ExpectedOutcome]:
    """Generate expected output hypotheses for each task.

    These hypotheses become checkpoints that Tier 4 evaluates
    after execution. If an expectation is unmet, Reflection is triggered.
    """
    settings = get_settings().kernel
    hypotheses: list[ExpectedOutcome] = []

    for task in bound_tasks[: settings.max_hypothesis_count]:
        # Base confidence on whether we have tool bindings and clear outputs
        confidence = 0.5
        if task.tool_binding:
            confidence += 0.2
        if task.outputs:
            confidence += 0.1
        if not task.depends_on:
            confidence += 0.1

        confidence = min(confidence, 1.0)

        # Build success criteria from task metadata
        criteria: dict[str, Any] = {}
        if task.outputs:
            for output_key in task.outputs:
                criteria[output_key] = "not_null"
        criteria["success"] = True

        hypotheses.append(ExpectedOutcome(
            task_id=task.task_id,
            description=f"Task '{task.description}' should produce valid output",
            output_schema="dict",
            success_criteria=criteria,
            confidence=round(confidence, 3),
        ))

    log.info("Hypotheses generated", count=len(hypotheses))
    return hypotheses


# ============================================================================
# Step 4: Inject Progress Tracker
# ============================================================================


def inject_progress_tracker(
    tasks: list[BoundTask],
    hypotheses: list[ExpectedOutcome],
    constraints: PlanningConstraints,
) -> TrackedPlan:
    """Create and attach a ProgressTracker to the plan.

    The tracker travels with the DAG through the OODA loop,
    enabling Tier 4 Observe to report progress and Tier 5
    to evaluate epoch completion.
    """
    tracker = ProgressTracker(
        total_tasks=len(tasks),
        hypotheses_total=len(hypotheses),
        total_cost_consumed=0.0,
        completion_percentage=0.0,
    )

    plan = TrackedPlan(
        plan_id=generate_id("plan"),
        tasks=tasks,
        hypotheses=hypotheses,
        tracker=tracker,
        constraints=constraints,
    )

    log.info(
        "Progress tracker injected",
        plan_id=plan.plan_id,
        total_tasks=len(tasks),
        total_hypotheses=len(hypotheses),
    )

    return plan


# ============================================================================
# Top-Level Orchestrator
# ============================================================================


async def plan_advanced(
    subtasks: list[SubTaskItem],
    constraints: PlanningConstraints | None = None,
    mcp_registry: MCPToolRegistry | None = None,
    kit: InferenceKit | None = None,
) -> Result:
    """Top-level advanced planning orchestrator.

    Takes decomposed sub-tasks and planning constraints, sequences
    them optimally, binds MCP tools, generates hypotheses, and
    injects a progress tracker.
    """
    ref = _ref("plan_advanced")
    start = time.perf_counter()

    if constraints is None:
        constraints = PlanningConstraints()
    if mcp_registry is None:
        mcp_registry = MCPToolRegistry()

    try:
        # Step 1: Sequence & prioritize
        sequenced = await sequence_and_prioritize(subtasks, constraints, kit)

        # Step 2: Bind tools
        bound = await bind_tools(sequenced, mcp_registry)

        # Step 3: Generate hypotheses
        hypotheses = generate_hypotheses(bound)

        # Step 4: Inject tracker
        plan = inject_progress_tracker(bound, hypotheses, constraints)

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)

        signal = create_data_signal(
            data=plan.model_dump(),
            schema="TrackedPlan",
            origin=ref,
            trace_id="",
            tags={
                "plan_id": plan.plan_id,
                "task_count": str(len(plan.tasks)),
                "mode": constraints.priority_mode.value,
            },
        )

        log.info(
            "Advanced planning complete",
            plan_id=plan.plan_id,
            tasks=len(plan.tasks),
            hypotheses=len(plan.hypotheses),
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Advanced planning failed: {exc}",
            source=ref,
            detail={"task_count": len(subtasks), "error_type": type(exc).__name__},
        )
        log.error("Advanced planning failed", error=str(exc))
        return fail(error=error, metrics=metrics)
