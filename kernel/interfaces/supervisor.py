from typing import Any, Protocol, runtime_checkable, Dict, Optional
from enum import Enum

class EscalationType(str, Enum):
    """Types of escalation."""
    ERROR = "error"
    CLARIFICATION = "clarification"
    APPROVAL = "approval"
    COMPLIANCE = "compliance"

@runtime_checkable
class Supervisor(Protocol):
    """Protocol for supervisor escalation."""
    
    async def escalate_to_human(
        self,
        escalation_type: EscalationType,
        source: str,
        context: Dict[str, Any],
        message: str
    ) -> Any:
        """Escalate a task/error to a human operator."""
        ...
