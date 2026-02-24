"""
Tier 4: Async Multitasking Module.

DAG parking, context switching, and deep sleep delegation
for efficient multi-task handling within the OODA loop.

Usage::

    from kernel.async_multitasking import manage_async_tasks

    result = await manage_async_tasks(node_result, dag, dag_queue, stm)
"""

from .engine import (
    check_async_requirement,
    manage_async_tasks,
    park_dag_state,
    register_wait_listener,
    request_deep_sleep,
    switch_context,
)
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

__all__ = [
    "manage_async_tasks",
    "check_async_requirement",
    "park_dag_state",
    "register_wait_listener",
    "switch_context",
    "request_deep_sleep",
    "DAGQueue",
    "DAGQueueEntry",
    "NextAction",
    "NextActionKind",
    "ParkingTicket",
    "SleepToken",
    "WaitHandle",
    "WaitMode",
]
