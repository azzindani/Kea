"""
Base types for the Cognition Pipeline.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable

from pydantic import BaseModel, Field

from kernel.io.output_schemas import WorkPackage
from kernel.memory.working_memory import WorkingMemory
from kernel.actions.cell_communicator import CellCommunicator
from kernel.memory.artifact_store import ArtifactStore
from shared.logging import get_logger

# Deferred import to avoid circular dependency — AwarenessEnvelope is only
# used as a type annotation and accessed at runtime, not at import time.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from kernel.awareness.context_fusion import AwarenessEnvelope

logger = get_logger(__name__)



class CyclePhase(str, Enum):
    """Current phase in the cognitive cycle."""
    PERCEIVE = "perceive"
    EXPLORE = "explore"
    FRAME = "frame"
    PLAN = "plan"
    EXECUTE = "execute"
    MONITOR = "monitor"
    ADAPT = "adapt"
    PACKAGE = "package"


@dataclass
class CycleContext:
    """Shared context passed between phases."""
    task_id: str
    task_text: str
    memory: WorkingMemory
    communicator: CellCommunicator
    
    # External hooks
    llm_call: Callable[[str, str], Awaitable[str]]
    tool_call: Callable[[str, dict], Awaitable[Any]]
    
    # State accumulators
    available_tools: list[dict[str, Any]] = field(default_factory=list)
    artifact_store: ArtifactStore = field(default_factory=ArtifactStore)
    framing: Any = None  # FramingResult
    plan: Any = None     # PlanResult
    execution_history: list[dict] = field(default_factory=list)
    tool_results: list[dict] = field(default_factory=list)
    monitor_result: Any = None

    # Situational Awareness (Phase 1 — injected from KernelCell._intake)
    awareness: AwarenessEnvelope | None = field(default=None)

    # Metrics
    start_time: datetime = field(default_factory=datetime.utcnow)
    step_count: int = 0
    tool_call_count: int = 0

    @property
    def elapsed_ms(self) -> float:
        return (datetime.utcnow() - self.start_time).total_seconds() * 1000


class BasePhase(ABC):
    """Abstract base class for a cognitive phase."""
    
    def __init__(self, context: CycleContext):
        self.context = context
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def run(self, **kwargs) -> Any:
        """Execute the phase logic."""
        pass

