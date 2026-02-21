"""
Supervisor Layer for Quality and Escalation.

Provides oversight capabilities:
- Quality gates for output validation
- Team health monitoring
- Human-in-the-loop escalation
- Load redistribution
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Awaitable

from shared.logging import get_logger


logger = get_logger(__name__)


class CheckResult(str, Enum):
    """Result of quality check."""
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class EscalationType(str, Enum):
    """Types of escalation."""
    QUALITY = "quality"       # Output quality issue
    RESOURCE = "resource"     # Resource constraint
    DECISION = "decision"     # Needs human decision
    ERROR = "error"           # Unrecoverable error
    TIMEOUT = "timeout"       # Task timeout


@dataclass
class Escalation:
    """Escalation request."""
    escalation_id: str
    escalation_type: EscalationType
    source_agent: str
    work_id: str | None
    context: dict[str, Any]
    message: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolution: str | None = None


EscalationHandler = Callable[[Escalation], Awaitable[None]]


class Supervisor:
    """
    Oversees team performance and escalations.
    
    Responsibilities:
    - Escalate issues to human when needed
    - Track pending resolutions
    """
    
    def __init__(self):
        self._escalation_handlers: list[EscalationHandler] = []
        self._pending_escalations: dict[str, Escalation] = {}
    
    def on_escalation(self, handler: EscalationHandler) -> None:
        """Register escalation handler."""
        self._escalation_handlers.append(handler)
    
    async def escalate_to_human(
        self,
        escalation_type: EscalationType,
        source_agent: str,
        context: dict[str, Any],
        message: str,
        work_id: str | None = None,
    ) -> str:
        """
        Escalate issue to human.
        
        Returns escalation ID for tracking.
        """
        import uuid
        
        escalation = Escalation(
            escalation_id=f"esc_{uuid.uuid4().hex[:8]}",
            escalation_type=escalation_type,
            source_agent=source_agent,
            work_id=work_id,
            context=context,
            message=message,
        )
        
        self._pending_escalations[escalation.escalation_id] = escalation
        logger.warning(f"Escalation {escalation.escalation_id}: {message}")
        
        # Notify handlers
        for handler in self._escalation_handlers:
            try:
                await handler(escalation)
            except Exception as e:
                logger.error(f"Escalation handler error: {e}")
        
        return escalation.escalation_id
    
    async def resolve_escalation(
        self,
        escalation_id: str,
        resolution: str,
    ) -> bool:
        """Resolve an escalation."""
        if escalation_id not in self._pending_escalations:
            return False
        
        escalation = self._pending_escalations[escalation_id]
        escalation.resolved = True
        escalation.resolution = resolution
        
        logger.info(f"Escalation {escalation_id} resolved: {resolution}")
        return True
    
    @property
    def pending_escalation_count(self) -> int:
        """Number of unresolved escalations."""
        return sum(1 for e in self._pending_escalations.values() if not e.resolved)


# Global supervisor instance
_supervisor: Supervisor | None = None


def get_supervisor() -> Supervisor:
    """Get or create global supervisor."""
    global _supervisor
    if _supervisor is None:
        _supervisor = Supervisor()
    return _supervisor

