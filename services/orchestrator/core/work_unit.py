"""
Work Unit Abstraction for Task Management.

Provides corporate-style task tracking with:
- WorkUnit: Atomic unit of work
- WorkBoard: Kanban-style management
- Priority and dependency tracking
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from shared.logging import get_logger


logger = get_logger(__name__)


class WorkType(str, Enum):
    """Types of work."""
    RESEARCH = "research"
    ANALYSIS = "analysis"
    REVIEW = "review"
    DECISION = "decision"
    SYNTHESIS = "synthesis"
    VALIDATION = "validation"
    EXECUTION = "execution"


class WorkStatus(str, Enum):
    """Work status states."""
    PENDING = "pending"         # Waiting to be assigned
    ASSIGNED = "assigned"       # Assigned to agent
    IN_PROGRESS = "in_progress" # Being worked on
    BLOCKED = "blocked"         # Waiting on dependency
    REVIEW = "review"           # Awaiting review
    COMPLETED = "completed"     # Done
    FAILED = "failed"           # Failed
    CANCELLED = "cancelled"     # Cancelled


class Priority(int, Enum):
    """Work priority levels."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


@dataclass
class WorkUnit:
    """
    Atomic unit of work (like a corporate task/ticket).
    
    Tracks:
    - Type and priority
    - Dependencies
    - Assignment and status
    - Results
    """
    work_id: str
    title: str
    work_type: WorkType
    description: str = ""
    priority: Priority = Priority.NORMAL
    deadline: datetime | None = None
    
    # Assignment
    assigned_to: str | None = None  # agent_id or team_id
    department_id: str | None = None
    
    # Dependencies
    dependencies: list[str] = field(default_factory=list)  # work_ids
    blocked_by: str | None = None  # work_id blocking this
    
    # Status
    status: WorkStatus = WorkStatus.PENDING
    progress: float = 0.0  # 0-1
    
    # Results
    result: Any = None
    error: str | None = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    
    @classmethod
    def create(
        cls,
        title: str,
        work_type: WorkType,
        description: str = "",
        priority: Priority = Priority.NORMAL,
        deadline: datetime | None = None,
    ) -> "WorkUnit":
        """Create new work unit."""
        return cls(
            work_id=f"work_{uuid.uuid4().hex[:8]}",
            title=title,
            work_type=work_type,
            description=description,
            priority=priority,
            deadline=deadline,
        )
    
    def assign(self, agent_id: str, department_id: str | None = None) -> None:
        """Assign work to agent."""
        self.assigned_to = agent_id
        self.department_id = department_id
        self.status = WorkStatus.ASSIGNED
        logger.debug(f"Work {self.work_id} assigned to {agent_id}")
    
    def start(self) -> None:
        """Mark work as started."""
        self.status = WorkStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()
        logger.debug(f"Work {self.work_id} started")
    
    def update_progress(self, progress: float) -> None:
        """Update progress (0-1)."""
        self.progress = min(1.0, max(0.0, progress))
    
    def complete(self, result: Any = None) -> None:
        """Mark work as completed."""
        self.status = WorkStatus.COMPLETED
        self.progress = 1.0
        self.result = result
        self.completed_at = datetime.utcnow()
        logger.info(f"Work {self.work_id} completed")
    
    def fail(self, error: str) -> None:
        """Mark work as failed."""
        self.status = WorkStatus.FAILED
        self.error = error
        self.completed_at = datetime.utcnow()
        logger.error(f"Work {self.work_id} failed: {error}")
    
    def block(self, blocked_by: str) -> None:
        """Mark work as blocked."""
        self.status = WorkStatus.BLOCKED
        self.blocked_by = blocked_by
        logger.warning(f"Work {self.work_id} blocked by {blocked_by}")
    
    @property
    def is_ready(self) -> bool:
        """Check if all dependencies are met."""
        return not self.dependencies or all(
            # Would need to check WorkBoard for dependency status
            False  # Placeholder - real implementation checks board
        )
    
    @property
    def duration(self) -> float | None:
        """Duration in seconds if completed."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class WorkBoard:
    """
    Kanban-style work management board.
    
    Provides:
    - Work queue management
    - Assignment and load balancing
    - Dependency resolution
    
    Example:
        board = WorkBoard()
        
        # Create work
        work = WorkUnit.create("Analyze Tesla", WorkType.ANALYSIS)
        board.add(work)
        
        # Assign to agent
        board.assign(work.work_id, "agent_123")
        
        # Get pending work
        pending = board.get_by_status(WorkStatus.PENDING)
    """
    
    def __init__(self):
        self._work: dict[str, WorkUnit] = {}
        self._by_status: dict[WorkStatus, set[str]] = {
            status: set() for status in WorkStatus
        }
        self._by_priority: dict[Priority, set[str]] = {
            priority: set() for priority in Priority
        }
    
    def add(self, work: WorkUnit) -> None:
        """Add work to board."""
        self._work[work.work_id] = work
        self._by_status[work.status].add(work.work_id)
        self._by_priority[work.priority].add(work.work_id)
        logger.debug(f"Added work {work.work_id} to board")
    
    def get(self, work_id: str) -> WorkUnit | None:
        """Get work by ID."""
        return self._work.get(work_id)
    
    def update_status(self, work_id: str, new_status: WorkStatus) -> bool:
        """Update work status."""
        work = self._work.get(work_id)
        if not work:
            return False
        
        # Update index
        self._by_status[work.status].discard(work_id)
        work.status = new_status
        self._by_status[new_status].add(work_id)
        
        return True
    
    def get_by_status(self, status: WorkStatus) -> list[WorkUnit]:
        """Get all work with status."""
        return [
            self._work[wid]
            for wid in self._by_status[status]
            if wid in self._work
        ]
    
    def get_next_pending(self) -> WorkUnit | None:
        """Get highest priority pending work."""
        for priority in Priority:
            work_ids = self._by_priority[priority] & self._by_status[WorkStatus.PENDING]
            if work_ids:
                return self._work[next(iter(work_ids))]
        return None
    
    def assign(self, work_id: str, agent_id: str, department_id: str | None = None) -> bool:
        """Assign work to agent."""
        work = self._work.get(work_id)
        if not work or work.status != WorkStatus.PENDING:
            return False
        
        work.assign(agent_id, department_id)
        self.update_status(work_id, WorkStatus.ASSIGNED)
        return True
    
    def complete(self, work_id: str, result: Any = None) -> bool:
        """Mark work as completed."""
        work = self._work.get(work_id)
        if not work:
            return False
        
        work.complete(result)
        self.update_status(work_id, WorkStatus.COMPLETED)
        
        # Unblock dependent work
        self._unblock_dependents(work_id)
        return True
    
    def _unblock_dependents(self, completed_work_id: str) -> None:
        """Unblock work that depended on completed work."""
        for work in self._work.values():
            if work.blocked_by == completed_work_id:
                work.blocked_by = None
                if work.status == WorkStatus.BLOCKED:
                    work.status = WorkStatus.PENDING
                    self.update_status(work.work_id, WorkStatus.PENDING)
                    logger.debug(f"Unblocked work {work.work_id}")
    
    @property
    def stats(self) -> dict:
        """Board statistics."""
        return {
            "total": len(self._work),
            "by_status": {
                status.value: len(self._by_status[status])
                for status in WorkStatus
            },
            "by_priority": {
                priority.name: len(self._by_priority[priority])
                for priority in Priority
            },
        }


# Global work board instance
_board: WorkBoard | None = None


def get_work_board() -> WorkBoard:
    """Get or create global work board."""
    global _board
    if _board is None:
        _board = WorkBoard()
    return _board
