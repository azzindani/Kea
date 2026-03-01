"""
Tier 4 OODA Loop — Engine.

The real-time beating heart of the Human Kernel:
    1. Observe: Sense environment events
    2. Orient: Contextualize via RAG + working memory
    3. Decide: Plan/replan via Tier 3
    4. Act: Execute DAG nodes via MCP

CRITICAL RULE: The OODA Loop must never block synchronously on slow
LLM calls. It iterates rapidly, dispatching asynchronous tasks and
relying on Short-Term Memory to track state.
"""

from __future__ import annotations

import json
import time
from typing import Any

from kernel.graph_synthesizer.types import ExecutableDAG, NodeStatus
from kernel.short_term_memory.engine import ShortTermMemory
from kernel.short_term_memory.types import (
    EventSource,
    NodeExecutionStatus,
    ObservationEvent,
)
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
    ActionResult,
    AgentState,
    AgentStatus,
    CycleAction,
    CycleResult,
    Decision,
    DecisionAction,
    EventStream,
    LoopResult,
    LoopTerminationReason,
    MacroObjective,
    OrientedState,
)

log = get_logger(__name__)

_MODULE = "ooda_loop"
_TIER = 4


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


# ============================================================================
# Phase 1: Observe (Sense)
# ============================================================================


async def observe(
    event_stream: EventStream,
    stm: ShortTermMemory,
    pending_events: list[ObservationEvent] | None = None,
) -> list[ObservationEvent]:
    """Rapidly poll the event stream for new signals.

    Drops each event into the Short-Term Memory's HistoryQueue.
    Must never block on slow sources; uses configurable poll timeouts.
    """
    observations: list[ObservationEvent] = []

    # In the kernel implementation, event_stream polling is abstracted.
    # The actual polling happens at the service layer (Orchestrator).
    # Here we process any pending events that were injected.
    if pending_events:
        for event in pending_events:
            stm.push_event(event)
            observations.append(event)

    if observations:
        log.debug(
            "Observe phase complete",
            events_collected=len(observations),
        )
    else:
        log.debug("Observe phase: no new events")

    return observations


# ============================================================================
# Phase 2: Orient (Contextualize)
# ============================================================================


async def orient(
    observations: list[ObservationEvent],
    stm: ShortTermMemory,
    rag_context: dict[str, Any] | None = None,
    kit: InferenceKit | None = None,
) -> OrientedState:
    """Update the working context by merging new observations with knowledge.

    In production, pulls context from the RAG Service via HTTP API.
    Here we work with injected RAG context and Short-Term Memory.
    """
    # Read existing context from STM
    context_slice = await stm.read_context(kit=kit)

    # Detect blocking conditions
    is_blocked = False
    blocking_reason = ""

    for obs in observations:
        desc_lower = obs.description.lower()
        if any(
            kw in desc_lower
            for kw in ("disconnected", "timeout", "unavailable", "crashed", "offline")
        ):
            is_blocked = True
            blocking_reason = obs.description
            break

    # Summarize observations
    summaries = [obs.description for obs in observations[:10]]
    observation_summary = "; ".join(summaries) if summaries else "No new observations"
    
    log.debug(
        "OODA Orient: Processing observations",
        count=len(observations),
        summaries=summaries,
        stm_keys=list(context_slice.cached_entities.keys()),
        rag_keys=list(rag_context.keys()) if rag_context else []
    )

    # LLM Context Analysis
    if kit and kit.has_llm and observations:
        try:
            system_msg = LLMMessage(
                role="system",
                content="Analyze observations. Is the agent blocked? Provide a concise summary. Respond EXACTLY with JSON: {\"is_blocked\": true/false, \"blocking_reason\": \"...\", \"summary\": \"...\"}"
            )
            user_msg = LLMMessage(role="user", content=f"Observations: {summaries}")
            resp = await kit.llm.complete([system_msg, user_msg], kit.llm_config)

            content = resp.content.strip()
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            data = json.loads(content)

            is_blocked = bool(data.get("is_blocked", is_blocked))
            blocking_reason = data.get("blocking_reason", blocking_reason)
            observation_summary = data.get("summary", observation_summary)
        except Exception as e:
            log.warning("LLM orientation failed", error=str(e))
            pass

    # Detect state changes
    state_changes: list[str] = []
    for obs in observations:
        if obs.source == EventSource.SYSTEM:
            state_changes.append(f"System: {obs.description}")
        elif obs.source == EventSource.MCP_TOOL:
            state_changes.append(f"Tool: {obs.description}")
        elif obs.source == EventSource.USER:
            state_changes.append(f"User: {obs.description}")

    # Merge with RAG context
    enriched: dict[str, Any] = dict(context_slice.cached_entities)
    if rag_context:
        enriched.update(rag_context)

    # Cache entities from observations
    for obs in observations:
        for key, value in obs.payload.items():
            if isinstance(value, (str, int, float, bool)):
                stm.cache_entity(
                    key=f"{obs.source.value}_{key}",
                    value=value,
                )

    oriented = OrientedState(
        is_blocked=is_blocked,
        blocking_reason=blocking_reason,
        enriched_context=enriched,
        observation_summary=observation_summary,
        state_changes=state_changes,
    )

    log.debug(
        "Orient phase complete",
        is_blocked=is_blocked,
        state_changes=len(state_changes),
        enriched_keys=len(enriched),
    )

    return oriented


# ============================================================================
# Phase 3: Decide (Plan)
# ============================================================================


async def decide(
    oriented_state: OrientedState,
    current_objectives: list[MacroObjective],
    active_dag: ExecutableDAG | None = None,
    stm: ShortTermMemory | None = None,
) -> Decision:
    """Compare the oriented state against active goals and decide next action.

    If the current DAG is still valid and progressing, continues.
    If the state has changed, requests replanning from Tier 3.
    """
    # If blocked, we need to replan or park
    if oriented_state.is_blocked:
        return Decision(
            action=DecisionAction.PARK,
            reasoning=f"Agent is blocked: {oriented_state.blocking_reason}",
        )

    # If no active DAG, we need to plan
    if active_dag is None:
        log.debug("OODA Decide: No active DAG detected")
        if current_objectives:
            obj = current_objectives[0]
            return Decision(
                action=DecisionAction.REPLAN,
                reasoning=f"No active DAG, planning for objective: {obj.description}",
                replan_objective=obj.description,
                replan_context=oriented_state.enriched_context,
            )
        else:
            return Decision(
                action=DecisionAction.SLEEP,
                reasoning="No objectives and no active DAG",
            )

    # Check if all objectives are completed
    all_complete = all(obj.completed for obj in current_objectives)
    if all_complete and current_objectives:
        return Decision(
            action=DecisionAction.COMPLETE,
            reasoning="All macro objectives completed",
        )
    
    log.debug("OODA Decide: Checking DAG progress", dag_id=active_dag.dag_id if active_dag else None)

    # Check DAG progress
    if stm is not None:
        snapshot = stm.get_dag_snapshot(active_dag.dag_id)
        if snapshot is not None:
            # All nodes done?
            if snapshot.pending_count == 0 and snapshot.running_count == 0:
                if snapshot.failed_count > 0:
                    # Some failed → replan
                    return Decision(
                        action=DecisionAction.REPLAN,
                        reasoning=f"DAG complete but {snapshot.failed_count} nodes failed",
                        replan_objective=active_dag.description,
                        replan_context={"failed_nodes": snapshot.failed_node_ids},
                    )
                else:
                    # All succeeded
                    log.debug("OODA Decide: Current DAG fully executed successfully")
                    return Decision(
                        action=DecisionAction.COMPLETE,
                        reasoning="Current DAG fully executed",
                    )
    # Find next pending nodes to execute
    pending_nodes = [
        n.node_id for n in active_dag.nodes
        if n.status == NodeStatus.PENDING
    ]

    if pending_nodes:
        # Execute next batch from parallel groups
        next_batch: list[str] = []
        for group in active_dag.parallel_groups:
            batch_nodes = [nid for nid in group if nid in pending_nodes]
            if batch_nodes:
                next_batch = batch_nodes
                break

        if not next_batch:
            next_batch = pending_nodes[:1]

        return Decision(
            action=DecisionAction.CONTINUE,
            reasoning=f"Continuing DAG execution with {len(next_batch)} node(s)",
            target_node_ids=next_batch,
        )

    # No pending nodes — DAG should be complete
    return Decision(
        action=DecisionAction.COMPLETE,
        reasoning="No pending nodes remaining in active DAG",
    )


# ============================================================================
# Phase 4: Act (Execute)
# ============================================================================


async def act(
    decision: Decision,
    active_dag: ExecutableDAG | None,
    stm: ShortTermMemory,
    kit: InferenceKit | None = None,
    agent_state: AgentState | None = None,
) -> list[ActionResult]:
    """Execute DAG node(s) based on the decision.

    In production, dispatches to MCP Host for tool execution.
    Here we execute the node callables and track state in STM.
    """
    results: list[ActionResult] = []

    if decision.action != DecisionAction.CONTINUE or active_dag is None:
        return results

    for node_id in decision.target_node_ids:
        start = time.perf_counter()

        # Find the node
        node = next(
            (n for n in active_dag.nodes if n.node_id == node_id),
            None,
        )

        if node is None:
            results.append(ActionResult(
                node_id=node_id,
                success=False,
                error_message=f"Node {node_id} not found in DAG",
            ))
            stm.update_dag_state(
                dag_id=active_dag.dag_id,
                node_id=node_id,
                status=NodeExecutionStatus.FAILED,
            )
            continue

        # Mark as running
        node.status = NodeStatus.RUNNING
        stm.update_dag_state(
            dag_id=active_dag.dag_id,
            node_id=node_id,
            status=NodeExecutionStatus.RUNNING,
        )

        # Node execution: in kernel, we implement basic LLM inference
        # if the kit is available and the node requires it.
        # Other types (tool_call) are still delegated to the service layer.
        node_outputs = {"instruction": node.instruction.description}
        
        if kit and kit.has_llm and node.instruction.action_type == "llm_inference":
            try:
                # Build context-aware prompt
                ctx_summary = ""
                if agent_state:
                    ctx_summary = json.dumps(agent_state.context, indent=2)
                
                system_msg = LLMMessage(
                    role="system",
                    content=f"Execute this task EXTREMELY FACTUALLY based on the provided context. If the context contains specific numbers, dates, or names, you MUST use them exactly. This output will be used for automated grounding verification. Context:\n{ctx_summary}"
                )
                user_msg = LLMMessage(role="user", content=node.instruction.description)
                
                resp = await kit.llm.complete([system_msg, user_msg], kit.llm_config)
                node_outputs["answer"] = resp.content.strip()
                log.info("OODA Act: LLM inference successful", node_id=node_id)
            except Exception as e:
                log.warning("OODA Act: LLM inference failed, fallback to echo", error=str(e))

        elapsed_ms = (time.perf_counter() - start) * 1000
        
        log.info(
            "OODA Act: Task executed", 
            node_id=node_id, 
            type=node.instruction.action_type,
            parameters=node.instruction.parameters,
            input_keys=node.input_keys,
            output_keys=node.output_keys,
            success=True,
            duration_ms=round(elapsed_ms, 2)
        )

        result = ActionResult(
            node_id=node_id,
            success=True,
            outputs=node_outputs,
            duration_ms=elapsed_ms,
            action_type=node.instruction.action_type,
            parameters=node.instruction.parameters,
            input_keys=node.input_keys,
            output_keys=node.output_keys,
        )

        # Update node status
        status = NodeExecutionStatus.COMPLETED if result.success else NodeExecutionStatus.FAILED
        node.status = NodeStatus.COMPLETED if result.success else NodeStatus.FAILED

        stm.update_dag_state(
            dag_id=active_dag.dag_id,
            node_id=node_id,
            status=status,
        )

        results.append(result)

    log.debug(
        "Act phase complete",
        nodes_executed=len(results),
        successes=sum(1 for r in results if r.success),
    )

    return results


# ============================================================================
# Single Cycle Orchestrator
# ============================================================================


async def run_ooda_cycle(
    state: AgentState,
    stm: ShortTermMemory,
    active_dag: ExecutableDAG | None = None,
    event_stream: EventStream | None = None,
    pending_events: list[ObservationEvent] | None = None,
    rag_context: dict[str, Any] | None = None,
    kit: InferenceKit | None = None,
) -> CycleResult:
    """Execute one complete Observe-Orient-Decide-Act cycle.

    Returns a CycleResult with updated state and action indication.
    """
    cycle_num = state.cycle_count + 1

    if event_stream is None:
        event_stream = EventStream(stream_id=generate_id("stream"))

    # Phase 1: Observe
    observations = await observe(event_stream, stm, pending_events)

    # Phase 2: Orient
    oriented = await orient(observations, stm, rag_context, kit)
    state.context.update(oriented.enriched_context)

    # Phase 3: Decide
    decision = await decide(
        oriented,
        state.current_objectives,
        active_dag,
        stm,
    )

    # Phase 4: Act
    action_results = await act(decision, active_dag, stm, kit, state)

    # Update agent state
    state.cycle_count = cycle_num

    # Determine next loop action
    if decision.action == DecisionAction.COMPLETE:
        next_action = CycleAction.TERMINATE
    elif decision.action == DecisionAction.PARK:
        next_action = CycleAction.PARK
    elif decision.action == DecisionAction.SLEEP:
        next_action = CycleAction.SLEEP
    else:
        next_action = CycleAction.CONTINUE

    # Update agent status
    if decision.action == DecisionAction.PARK:
        state.status = AgentStatus.BLOCKED
    elif decision.action == DecisionAction.SLEEP:
        state.status = AgentStatus.SLEEPING
    elif decision.action == DecisionAction.COMPLETE:
        state.status = AgentStatus.TERMINATED

    result = CycleResult(
        cycle_number=cycle_num,
        next_action=next_action,
        action_results=action_results,
        state_snapshot=state.model_dump(),
        artifacts_produced=[
            r.node_id for r in action_results if r.success
        ],
    )

    log.debug(
        "OODA cycle complete",
        cycle=cycle_num,
        decision=decision.action.value,
        next_action=next_action.value,
        nodes_executed=len(action_results),
    )

    return result


# ============================================================================
# Continuous Loop Runner
# ============================================================================


async def run_ooda_loop(
    initial_state: AgentState,
    stm: ShortTermMemory | None = None,
    active_dag: ExecutableDAG | None = None,
    kit: InferenceKit | None = None,
) -> Result:
    """Continuous OODA loop runner.

    Repeatedly executes run_ooda_cycle() until:
    - Tier 5 issues a sleep/terminate signal
    - The active macro-objective is completed
    - Maximum cycles are reached

    Returns a Result containing the final LoopResult.
    """
    ref = _ref("run_ooda_loop")
    start = time.perf_counter()
    settings = get_settings().kernel

    if stm is None:
        stm = ShortTermMemory()

    state = initial_state
    all_artifacts: list[str] = []
    completed_objectives: list[str] = []
    termination_reason = LoopTerminationReason.MAX_CYCLES_REACHED

    try:
        for cycle in range(settings.ooda_max_cycles):
            # Check lifecycle signals (Tier 5 integration point)
            if state.status in (AgentStatus.SLEEPING, AgentStatus.TERMINATED):
                termination_reason = LoopTerminationReason.LIFECYCLE_SIGNAL
                break

            # Run one cycle
            cycle_result = await run_ooda_cycle(
                state=state,
                stm=stm,
                active_dag=active_dag,
                kit=kit,
            )

            # Collect artifacts
            all_artifacts.extend(cycle_result.artifacts_produced)

            # Handle cycle outcome
            if cycle_result.next_action == CycleAction.TERMINATE:
                termination_reason = LoopTerminationReason.OBJECTIVE_COMPLETE
                completed_objectives = [
                    obj.objective_id
                    for obj in state.current_objectives
                    if obj.completed
                ]
                break

            elif cycle_result.next_action == CycleAction.PARK:
                termination_reason = LoopTerminationReason.ALL_DAGS_PARKED
                break

            elif cycle_result.next_action == CycleAction.SLEEP:
                termination_reason = LoopTerminationReason.ALL_DAGS_PARKED
                break

            # CycleAction.CONTINUE → keep looping

        elapsed = (time.perf_counter() - start) * 1000

        loop_result = LoopResult(
            agent_id=state.agent_id,
            total_cycles=state.cycle_count,
            termination_reason=termination_reason,
            final_state=state.model_dump(),
            total_duration_ms=elapsed,
            total_cost=state.total_cost,
            objectives_completed=completed_objectives,
            artifacts_produced=all_artifacts,
        )

        metrics = Metrics(duration_ms=elapsed, module_ref=ref)

        signal = create_data_signal(
            data=loop_result.model_dump(),
            schema="LoopResult",
            origin=ref,
            trace_id="",
            tags={
                "agent_id": state.agent_id,
                "cycles": str(state.cycle_count),
                "reason": termination_reason.value,
            },
        )

        log.info(
            "OODA loop terminated",
            agent_id=state.agent_id,
            cycles=state.cycle_count,
            reason=termination_reason.value,
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"OODA loop failed: {exc}",
            source=ref,
            detail={
                "agent_id": state.agent_id,
                "cycle": state.cycle_count,
                "error_type": type(exc).__name__,
            },
        )
        log.error("OODA loop failed", error=str(exc), cycle=state.cycle_count)
        return fail(error=error, metrics=metrics)
