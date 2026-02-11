"""
Guardrails — compliance gate for tool execution.

Wraps the Swarm Manager's ComplianceEngine as a module-level singleton so
researcher_node can call check_tool_call() before dispatching any tool batch.
Failed compliance checks feed into the existing error_feedback channel rather
than raising exceptions, keeping the self-correction loop intact.
"""

from __future__ import annotations

from shared.logging import get_logger

logger = get_logger(__name__)

_engine = None


def _get_engine():
    """Lazy-init the compliance engine singleton."""
    global _engine
    if _engine is None:
        try:
            from services.swarm_manager.core.compliance import get_compliance_engine

            _engine = get_compliance_engine()
        except Exception as e:
            logger.warning(f"Compliance engine unavailable: {e}")
    return _engine


async def check_tool_call(tool_name: str, arguments: dict) -> list[dict]:
    """
    Gate a single tool call through the compliance engine.

    Returns a list of violation dicts (empty = passed).
    Each violation has keys: check_id, severity, message.
    Violations are meant to be appended to error_feedback, not raised.
    """
    engine = _get_engine()
    if engine is None:
        return []

    try:
        report = await engine.check_operation(
            operation="tool_call",
            context={"tool_name": tool_name, "arguments": arguments},
        )
        if report.passed:
            return []
        return [
            {
                "check_id": issue.check_id,
                "severity": issue.severity.value,
                "message": issue.message,
            }
            for issue in report.issues
        ]
    except Exception as e:
        logger.warning(f"Compliance check failed (non-blocking): {e}")
        return []
