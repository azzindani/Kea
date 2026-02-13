"""
Shared Audit Utilities.

Provides AuditEventType enum and the @audited decorator for all services.
Audit events are logged via the Vault service REST API (POST /audit/logs)
rather than direct database access, preserving microservice boundaries.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from enum import Enum
from functools import wraps

from shared.logging import get_logger

logger = get_logger(__name__)


class AuditEventType(Enum):
    """Types of auditable events."""

    # Query lifecycle
    QUERY_RECEIVED = "query_received"
    QUERY_CLASSIFIED = "query_classified"
    QUERY_COMPLETED = "query_completed"

    # Tool operations
    TOOL_CALLED = "tool_called"
    TOOL_RESULT = "tool_result"
    TOOL_ERROR = "tool_error"

    # Data operations
    DATA_ACCESSED = "data_accessed"
    DATA_MODIFIED = "data_modified"
    DATA_DELETED = "data_deleted"

    # Decisions
    DECISION_MADE = "decision_made"
    DECISION_OVERRIDDEN = "decision_overridden"

    # Human in the loop
    ESCALATION_CREATED = "escalation_created"
    ESCALATION_RESOLVED = "escalation_resolved"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"

    # Security
    SECURITY_CHECK = "security_check"
    SECURITY_VIOLATION = "security_violation"
    ACCESS_DENIED = "access_denied"

    # System
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    CONFIG_CHANGED = "config_changed"
    ERROR = "error"


async def log_audit_event(
    event_type: AuditEventType,
    action: str,
    actor: str = "system",
    resource: str = "",
    details: dict | None = None,
    parent_id: str = "",
    session_id: str = "",
) -> str:
    """
    Log an audit event via Vault REST API.

    Returns the entry ID on success, or an empty string if Vault is unreachable.
    This call is non-blocking — failures are logged as debug and swallowed.
    """
    try:
        import httpx

        from shared.service_registry import ServiceName, ServiceRegistry

        vault_url = ServiceRegistry.get_url(ServiceName.VAULT)
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.post(
                f"{vault_url}/audit/logs",
                json={
                    "event_type": event_type.value,
                    "action": action,
                    "actor": actor,
                    "resource": resource,
                    "details": details or {},
                    "parent_id": parent_id,
                    "session_id": session_id,
                },
            )
            if resp.status_code == 200:
                return resp.json().get("entry_id", "")
    except Exception as e:
        logger.debug(f"Audit log skipped (non-blocking): {e}")
    return ""


async def _log_audit_event(event_type: AuditEventType, action: str, details: dict) -> None:
    """Internal helper used by the @audited decorator."""
    await log_audit_event(event_type=event_type, action=action, details=details)


def audited(
    event_type: AuditEventType,
    action_template: str = "{func_name} called",
    include_args: bool = False,
    include_result: bool = False,
) -> Callable:
    """
    Decorator to automatically audit function calls via Vault REST API.

    Audit events are fire-and-forget — they never block or fail the caller.

    Example:
        @audited(AuditEventType.TOOL_CALLED, "Called {func_name}")
        async def my_tool(query: str):
            return result
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            action = action_template.format(func_name=func.__name__)
            details: dict = {}
            if include_args:
                details["args"] = str(args)[:200]
                details["kwargs"] = {k: str(v)[:100] for k, v in kwargs.items()}

            # Log start — fire and forget
            asyncio.create_task(_log_audit_event(event_type, f"Starting: {action}", details))

            try:
                result = await func(*args, **kwargs)
                result_details: dict = {"status": "success"}
                if include_result:
                    result_details["result"] = str(result)[:500]
                asyncio.create_task(
                    _log_audit_event(event_type, f"Completed: {action}", result_details)
                )
                return result
            except Exception as exc:
                asyncio.create_task(
                    _log_audit_event(
                        event_type,
                        f"Failed: {action}",
                        {"error": str(exc)[:300]},
                    )
                )
                raise

        return wrapper

    return decorator
