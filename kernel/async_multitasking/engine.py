"""
Tier 4 Async Multitasking — Engine.

DAG parking, context switching, and deep sleep delegation:
    1. Check if a node result requires async waiting
    2. Park current DAG state to Short-Term Memory
    3. Register wait listeners (webhook/poll)
    4. Switch context to next priority DAG
    5. Request deep sleep from Tier 5 if no actionable work
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

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

from kernel.short_term_memory.engine import ShortTermMemory
from kernel.short_term_memory.types import NodeExecutionStatus
from kernel.graph_synthesizer.types import ExecutableDAG
from kernel.ooda_loop.types import ActionResult

from .types import (
    DAGQueue,
    DAGQueueEntry,
    NextAction,
    NextActionKind,
    ParkingTicket,
    SleepToken,
    WaitHandle,
    WaitMode,
)

log = get_logger(__name__)

_MODULE = "async_multitasking"
_TIER = 4


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


# ============================================================================
# Step 1: Check Async Requirement
# ============================================================================


def check_async_requirement(node_result: ActionResult) -> bool:
    """Inspect the action result to determine if async waiting is needed.

    Returns True if the result contains a Job ID, polling URL,
    or webhook registration handle (deferred result).
    """
    if node_result.is_async:
        return True
    if node_result.job_id is not None:
        return True
    if node_result.polling_url is not None:
        return True
    return False


# ============================================================================
# Step 2: Park DAG State
# ============================================================================


async def park_dag_state(
    dag: ExecutableDAG,
    stm: ShortTermMemory,
    node_result: ActionResult,
) -> ParkingTicket:
    """Save the entire DAG state to Short-Term Memory's waiting queue.

    Returns a ParkingTicket for later resumption.
    """
    # Update the node status to PARKED
    stm.update_dag_state(
        dag_id=dag.dag_id,
        node_id=node_result.node_id,
        status=NodeExecutionStatus.PARKED,
    )

    # Determine resume event type
    resume_event = "job_complete"
    if node_result.polling_url:
        resume_event = "poll_complete"
    elif node_result.job_id:
        resume_event = f"job_{node_result.job_id}_complete"

    ticket = ParkingTicket(
        ticket_id=generate_id("ticket"),
        dag_id=dag.dag_id,
        parked_at_node_id=node_result.node_id,
        resume_event_type=resume_event,
        state_snapshot=dag.state.model_dump(),
        parked_utc=datetime.now(timezone.utc).isoformat(),
    )

    log.info(
        "DAG parked",
        dag_id=dag.dag_id,
        ticket_id=ticket.ticket_id,
        parked_at=node_result.node_id,
        resume_event=resume_event,
    )

    return ticket


# ============================================================================
# Step 3: Register Wait Listener
# ============================================================================


async def register_wait_listener(
    parking_ticket: ParkingTicket,
    node_result: ActionResult,
) -> WaitHandle:
    """Register an event listener for the parked DAG's completion.

    Supports webhook (push) and poll (pull) modes.
    """
    settings = get_settings().kernel

    # Determine wait mode from result metadata
    if node_result.polling_url:
        wait_mode = WaitMode.POLL
        poll_url = node_result.polling_url
    elif node_result.job_id:
        wait_mode = WaitMode.WEBHOOK
        poll_url = None
    else:
        wait_mode = WaitMode.TIMER
        poll_url = None

    handle = WaitHandle(
        handle_id=generate_id("handle"),
        ticket_id=parking_ticket.ticket_id,
        wait_mode=wait_mode,
        poll_url=poll_url,
        poll_interval_ms=settings.async_poll_interval_ms,
        registered_utc=datetime.now(timezone.utc).isoformat(),
    )

    log.info(
        "Wait listener registered",
        handle_id=handle.handle_id,
        ticket_id=parking_ticket.ticket_id,
        mode=wait_mode.value,
    )

    return handle


# ============================================================================
# Step 4: Context Switch
# ============================================================================


async def switch_context(dag_queue: DAGQueue) -> str | None:
    """Load the next highest-priority DAG from the queue.

    Returns the DAG ID to switch to, or None if the queue
    has no actionable entries (all parked/empty).
    """
    # Find the highest-priority non-parked entry
    active_entries = [
        entry for entry in dag_queue.entries
        if not entry.is_parked
    ]

    if not active_entries:
        log.info("No actionable DAGs in queue, signaling for sleep")
        return None

    # Sort by priority (lower = higher priority)
    active_entries.sort(key=lambda e: e.priority)
    selected = active_entries[0]

    log.info(
        "Context switch",
        target_dag=selected.dag_id,
        priority=selected.priority,
        remaining_active=len(active_entries) - 1,
    )

    return selected.dag_id


# ============================================================================
# Step 5: Request Deep Sleep
# ============================================================================


async def request_deep_sleep(
    parked_tickets: list[ParkingTicket],
) -> SleepToken:
    """Signal that there is no actionable work available.

    In production, this would call Tier 5 Lifecycle Controller API.
    Currently packages the sleep token for upstream consumption.
    """
    wake_triggers = list(set(
        ticket.resume_event_type for ticket in parked_tickets
    ))

    token = SleepToken(
        token_id=generate_id("sleep"),
        wake_triggers=wake_triggers,
        parked_dag_count=len(parked_tickets),
        entered_sleep_utc=datetime.now(timezone.utc).isoformat(),
    )

    log.info(
        "Deep sleep requested",
        token_id=token.token_id,
        parked_dags=len(parked_tickets),
        wake_triggers=wake_triggers,
    )

    return token


# ============================================================================
# Top-Level Orchestrator
# ============================================================================


async def manage_async_tasks(
    node_result: ActionResult,
    dag: ExecutableDAG,
    dag_queue: DAGQueue,
    stm: ShortTermMemory,
) -> Result:
    """Top-level async task manager.

    Called by the OODA Act phase when a node produces a long-running
    result. Checks if async waiting is needed, parks the DAG if so,
    and either switches context or requests deep sleep.
    """
    ref = _ref("manage_async_tasks")
    start = time.perf_counter()

    try:
        # Step 1: Check if async handling is needed
        needs_async = check_async_requirement(node_result)

        if not needs_async:
            # Synchronous result — no action needed
            next_action = NextAction(
                kind=NextActionKind.CONTINUE_CURRENT,
                reasoning="Node completed synchronously, continuing current DAG",
            )
        else:
            # Step 2: Park the DAG
            ticket = await park_dag_state(dag, stm, node_result)

            # Mark the DAG as parked in the queue
            for entry in dag_queue.entries:
                if entry.dag_id == dag.dag_id:
                    entry.is_parked = True
                    entry.parking_ticket = ticket
                    break
            else:
                # Add to queue if not already present
                dag_queue.entries.append(DAGQueueEntry(
                    dag_id=dag.dag_id,
                    is_parked=True,
                    parking_ticket=ticket,
                    description=dag.description,
                ))

            # Step 3: Register wait listener
            await register_wait_listener(ticket, node_result)

            # Step 4: Try context switch
            next_dag_id = await switch_context(dag_queue)

            if next_dag_id is not None:
                next_action = NextAction(
                    kind=NextActionKind.SWITCH_CONTEXT,
                    target_dag_id=next_dag_id,
                    reasoning=f"Current DAG parked, switching to {next_dag_id}",
                )
            else:
                # Step 5: No actionable work → deep sleep
                parked_tickets = [
                    entry.parking_ticket
                    for entry in dag_queue.entries
                    if entry.is_parked and entry.parking_ticket is not None
                ]
                sleep_token = await request_deep_sleep(parked_tickets)

                next_action = NextAction(
                    kind=NextActionKind.DEEP_SLEEP,
                    reasoning=f"All DAGs parked, entering deep sleep (token: {sleep_token.token_id})",
                )

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)

        signal = create_data_signal(
            data=next_action.model_dump(),
            schema="NextAction",
            origin=ref,
            trace_id="",
            tags={
                "kind": next_action.kind.value,
                "async_required": str(needs_async),
            },
        )

        log.info(
            "Async task management complete",
            action=next_action.kind.value,
            async_required=needs_async,
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Async task management failed: {exc}",
            source=ref,
            detail={"node_id": node_result.node_id, "error_type": type(exc).__name__},
        )
        log.error("Async task management failed", error=str(exc))
        return fail(error=error, metrics=metrics)
