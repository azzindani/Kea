"""
Resource Governor   Adaptive Budget Control & Execution Governance.

Provides intelligent resource management for the kernel cell hierarchy:

1. **Dynamic Budget Reallocation**   When a child finishes under-budget,
   its surplus is redistributed to siblings still working.

2. **Preemptive Cancellation**   Cancels low-value or stalled children
   before they exhaust the parent's budget.

3. **Execution Telemetry**   Real-time tracking of where tokens are
   being spent, enabling data-driven replanning.

4. **Escalation Handling**   Structured responses to child escalations
   with configurable recovery strategies.

5. **Adaptive Throttling**   Integrates with GracefulDegrader to reduce
   parallelism under resource pressure.

The Governor sits above the DelegationProtocol and wraps the main
execution lifecycle in KernelCell.process().

Architecture::

     
                ResourceGovernor               
            
          BudgetLedger (per-child spend)       
          EscalationHandler (recovery)         
          ChildMonitor (health checks)         
            
                                               
       rebalance() cancel_stalled() govern()   
     

Version: 2.0.0   Part of Kernel Brain Upgrade (Phase 4)
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Awaitable, Callable

from pydantic import BaseModel, Field

from shared.logging import get_logger

from kernel.io.message_bus import (
    MessageBus,
    MessageChannel,
    MessagePriority,
    get_message_bus,
)

logger = get_logger(__name__)


# ============================================================================
# Budget Ledger   Per-Child Token Tracking
# ============================================================================


@dataclass
class ChildBudgetEntry:
    """Tracks a single child's budget allocation and spending."""

    child_id: str
    subtask_id: str = ""
    allocated: int = 0
    consumed: int = 0
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    status: str = "running"  # running | completed | failed | cancelled

    @property
    def surplus(self) -> int:
        """Unspent budget that can be reclaimed."""
        return max(0, self.allocated - self.consumed)

    @property
    def utilization(self) -> float:
        """Fraction of allocated budget consumed."""
        if self.allocated == 0:
            return 0.0
        return min(1.0, self.consumed / self.allocated)

    @property
    def elapsed_ms(self) -> float:
        """Milliseconds since the child started."""
        end = self.completed_at or datetime.utcnow()
        return (end - self.started_at).total_seconds() * 1000

    @property
    def is_active(self) -> bool:
        """Still running?"""
        return self.status == "running"


class BudgetLedger:
    """
    Centralized tracking of all budget allocations in a delegation.

    The parent uses this to make budget rebalancing decisions:
    which children are overspending? Which have surplus?
    """

    def __init__(self, total_budget: int) -> None:
        self.total_budget = total_budget
        self.entries: dict[str, ChildBudgetEntry] = {}
        self._rebalance_count: int = 0

    def register_child(
        self,
        child_id: str,
        subtask_id: str,
        allocated: int,
    ) -> None:
        """Record a new child allocation."""
        self.entries[child_id] = ChildBudgetEntry(
            child_id=child_id,
            subtask_id=subtask_id,
            allocated=allocated,
        )

    def record_consumption(self, child_id: str, tokens: int) -> None:
        """Update a child's token consumption."""
        entry = self.entries.get(child_id)
        if entry and entry.is_active:
            entry.consumed += tokens

    def mark_completed(
        self,
        child_id: str,
        tokens_used: int = 0,
    ) -> int:
        """
        Mark a child as completed and return its surplus.

        The surplus is available for redistribution.
        """
        entry = self.entries.get(child_id)
        if not entry:
            return 0

        entry.status = "completed"
        entry.completed_at = datetime.utcnow()
        if tokens_used > 0:
            entry.consumed = tokens_used

        surplus = entry.surplus
        logger.debug(
            f"Child {child_id} completed: "
            f"used {entry.consumed}/{entry.allocated}, surplus={surplus}"
        )
        return surplus

    def mark_failed(self, child_id: str) -> int:
        """Mark a child as failed and return its unspent budget."""
        entry = self.entries.get(child_id)
        if not entry:
            return 0
        entry.status = "failed"
        entry.completed_at = datetime.utcnow()
        return entry.surplus

    def mark_cancelled(self, child_id: str) -> int:
        """Mark a child as cancelled and return its unspent budget."""
        entry = self.entries.get(child_id)
        if not entry:
            return 0
        entry.status = "cancelled"
        entry.completed_at = datetime.utcnow()
        return entry.surplus

    #   Queries  

    @property
    def active_children(self) -> list[ChildBudgetEntry]:
        """Children still running."""
        return [e for e in self.entries.values() if e.is_active]

    @property
    def total_allocated(self) -> int:
        """Total tokens allocated to children."""
        return sum(e.allocated for e in self.entries.values())

    @property
    def total_consumed(self) -> int:
        """Total tokens consumed by all children."""
        return sum(e.consumed for e in self.entries.values())

    @property
    def total_surplus(self) -> int:
        """Total reclaimable surplus across completed/cancelled children."""
        return sum(
            e.surplus for e in self.entries.values()
            if not e.is_active
        )

    @property
    def reclaimable_budget(self) -> int:
        """Budget from completed children that can be given to active ones."""
        return sum(
            e.surplus for e in self.entries.values()
            if e.status in ("completed", "cancelled", "failed")
        )

    def slowest_child(self) -> ChildBudgetEntry | None:
        """Active child that has been running the longest."""
        active = self.active_children
        if not active:
            return None
        return max(active, key=lambda e: e.elapsed_ms)

    def most_expensive_child(self) -> ChildBudgetEntry | None:
        """Active child using the most tokens."""
        active = self.active_children
        if not active:
            return None
        return max(active, key=lambda e: e.consumed)

    def stalled_children(self, max_duration_ms: float = 30_000) -> list[ChildBudgetEntry]:
        """Children that have been running longer than the threshold."""
        return [
            e for e in self.active_children
            if e.elapsed_ms > max_duration_ms
        ]

    def to_summary(self) -> dict[str, Any]:
        """Human-readable summary of budget state."""
        return {
            "total_budget": self.total_budget,
            "total_allocated": self.total_allocated,
            "total_consumed": self.total_consumed,
            "total_surplus": self.total_surplus,
            "active_count": len(self.active_children),
            "completed_count": sum(
                1 for e in self.entries.values() if e.status == "completed"
            ),
            "failed_count": sum(
                1 for e in self.entries.values() if e.status == "failed"
            ),
            "cancelled_count": sum(
                1 for e in self.entries.values() if e.status == "cancelled"
            ),
            "rebalance_count": self._rebalance_count,
        }


# ============================================================================
# Escalation Models
# ============================================================================


class EscalationSeverity(str, Enum):
    """How critical is the escalation?"""

    LOW = "low"           # Informational, child can continue
    MEDIUM = "medium"     # Needs guidance, child is blocked
    HIGH = "high"         # Critical issue, child should stop
    CRITICAL = "critical" # System-level failure, abort delegation


class EscalationStrategy(str, Enum):
    """How to handle an escalation."""

    GUIDE = "guide"           # Provide guidance and let child continue
    REASSIGN = "reassign"     # Cancel child, create new one
    ABSORB = "absorb"         # Parent handles it directly
    SKIP = "skip"             # Skip the subtask entirely
    ESCALATE_UP = "escalate"  # Escalate to grandparent


@dataclass
class EscalationRecord:
    """Record of an escalation and its resolution."""

    child_id: str
    subtask_id: str
    severity: EscalationSeverity
    reason: str
    context: str = ""
    strategy: EscalationStrategy = EscalationStrategy.GUIDE
    response: str = ""
    resolved: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)


# ============================================================================
# Resource Governor
# ============================================================================


class ResourceGovernor:
    """
    Adaptive resource controller for a delegation session.

    The governor monitors child cell health and budget usage,
    making real-time decisions about:
    - Budget rebalancing (surplus   needy siblings)
    - Stalled child cancellation
    - Escalation handling
    - Execution telemetry

    Usage::

        governor = ResourceGovernor(
            parent_cell_id="analyst-42",
            total_budget=30000,
        )

        # Register children as they're spawned
        governor.register_child("child-1", "research_task", allocated=5000)

        # Periodic governance (call between phases)
        actions = await governor.govern()

        # Handle escalation
        record = await governor.handle_escalation(
            child_id="child-1",
            reason="Can't find the data",
            severity=EscalationSeverity.MEDIUM,
        )

        # Final telemetry
        telemetry = governor.get_telemetry()
    """

    def __init__(
        self,
        parent_cell_id: str,
        total_budget: int,
        llm_call: Callable[..., Awaitable[Any]] | None = None,
        bus: MessageBus | None = None,
        stall_threshold_ms: float = 30_000,
        low_budget_threshold: float = 0.1,
    ) -> None:
        self.parent_cell_id = parent_cell_id
        self.ledger = BudgetLedger(total_budget)
        self.llm_call = llm_call
        self._bus = bus or get_message_bus()

        # Thresholds
        self.stall_threshold_ms = stall_threshold_ms
        self.low_budget_threshold = low_budget_threshold

        # Escalation tracking
        self.escalations: list[EscalationRecord] = []
        self._governance_cycles: int = 0

        # Actions log
        self._actions_taken: list[dict[str, Any]] = []

    #   Child Lifecycle  

    def register_child(
        self,
        child_id: str,
        subtask_id: str,
        allocated: int,
    ) -> None:
        """Register a new child for governance tracking."""
        self.ledger.register_child(child_id, subtask_id, allocated)

    def child_completed(
        self,
        child_id: str,
        tokens_used: int = 0,
    ) -> int:
        """
        Record child completion and return surplus for redistribution.

        Returns:
            Number of surplus tokens reclaimed.
        """
        return self.ledger.mark_completed(child_id, tokens_used)

    def child_failed(self, child_id: str) -> int:
        """Record child failure and return unspent budget."""
        return self.ledger.mark_failed(child_id)

    #   Main Governance Loop  

    async def govern(self) -> list[dict[str, Any]]:
        """
        Run one governance cycle.

        Checks for:
        1. Stalled children   cancel them
        2. Budget pressure   rebalance
        3. Critical escalations   abort delegation

        Returns:
            List of actions taken (for logging/telemetry).
        """
        self._governance_cycles += 1
        actions: list[dict[str, Any]] = []

        #   Check for stalled children  
        stalled = self.ledger.stalled_children(self.stall_threshold_ms)
        for entry in stalled:
            logger.warning(
                f"Governor: Child {entry.child_id} stalled "
                f"({entry.elapsed_ms:.0f}ms, "
                f"{entry.utilization:.0%} budget used)"
            )
            action = {
                "type": "stall_warning",
                "child_id": entry.child_id,
                "elapsed_ms": entry.elapsed_ms,
                "utilization": entry.utilization,
            }

            # If budget utilization is high and time is long, cancel
            if entry.utilization > 0.8 and entry.elapsed_ms > self.stall_threshold_ms * 2:
                await self._cancel_child(
                    entry.child_id,
                    reason="Budget exhausted and exceeding time limit",
                )
                action["type"] = "cancelled_stalled"
                reclaimed = self.ledger.mark_cancelled(entry.child_id)
                action["reclaimed"] = reclaimed

            actions.append(action)

        #   Budget rebalancing  
        reclaimable = self.ledger.reclaimable_budget
        active = self.ledger.active_children

        if reclaimable > 0 and active:
            rebalance_actions = self._rebalance(reclaimable, active)
            actions.extend(rebalance_actions)

        #   Low budget warning  
        total_remaining = self.ledger.total_budget - self.ledger.total_consumed
        if total_remaining > 0:
            budget_ratio = total_remaining / self.ledger.total_budget
            if budget_ratio < self.low_budget_threshold:
                logger.warning(
                    f"Governor: Low budget ({budget_ratio:.0%} remaining)"
                )
                actions.append({
                    "type": "low_budget_warning",
                    "remaining_ratio": budget_ratio,
                    "remaining_tokens": total_remaining,
                })

        self._actions_taken.extend(actions)
        return actions

    #   Budget Rebalancing  

    def _rebalance(
        self,
        available: int,
        active: list[ChildBudgetEntry],
    ) -> list[dict[str, Any]]:
        """
        Redistribute surplus budget to active children.

        Strategy: proportional allocation based on each child's
        remaining work (inverse of utilization).
        """
        if not active or available <= 0:
            return []

        self.ledger._rebalance_count += 1
        actions: list[dict[str, Any]] = []

        # Calculate need scores: children with lower utilization
        # are closer to done and need less extra budget.
        needs: list[tuple[ChildBudgetEntry, float]] = []
        for entry in active:
            # Higher utilization = more likely to need extra budget
            need_score = entry.utilization
            needs.append((entry, need_score))

        total_need = sum(n for _, n in needs)
        if total_need <= 0:
            # Even distribution if all utilizations are 0
            per_child = available // len(active)
            for entry in active:
                entry.allocated += per_child
                actions.append({
                    "type": "budget_rebalance",
                    "child_id": entry.child_id,
                    "extra_tokens": per_child,
                })
            return actions

        # Proportional distribution
        for entry, need in needs:
            share = int(available * (need / total_need))
            if share > 0:
                entry.allocated += share
                actions.append({
                    "type": "budget_rebalance",
                    "child_id": entry.child_id,
                    "extra_tokens": share,
                    "new_allocated": entry.allocated,
                })

        logger.info(
            f"Governor: Rebalanced {available} tokens across "
            f"{len(active)} active children"
        )

        return actions

    #   Escalation Handling  

    async def handle_escalation(
        self,
        child_id: str,
        reason: str,
        severity: EscalationSeverity = EscalationSeverity.MEDIUM,
        context: str = "",
    ) -> EscalationRecord:
        """
        Handle an escalation from a child cell.

        Determines the appropriate strategy based on severity
        and available budget.

        Returns:
            EscalationRecord with the chosen strategy and response.
        """
        entry = self.ledger.entries.get(child_id)
        subtask_id = entry.subtask_id if entry else "unknown"

        record = EscalationRecord(
            child_id=child_id,
            subtask_id=subtask_id,
            severity=severity,
            reason=reason,
            context=context,
        )

        # Determine strategy based on severity
        if severity == EscalationSeverity.CRITICAL:
            record.strategy = EscalationStrategy.ESCALATE_UP
            record.response = (
                "Critical issue detected. Escalating to parent level."
            )
            await self._cancel_child(child_id, reason="Critical escalation")
            if entry:
                self.ledger.mark_cancelled(child_id)

        elif severity == EscalationSeverity.HIGH:
            # High severity: try to guide, but prepare to skip
            if self.llm_call and self._can_afford_guidance():
                record.strategy = EscalationStrategy.GUIDE
                record.response = await self._generate_guidance(
                    reason, context, subtask_id,
                )
            else:
                record.strategy = EscalationStrategy.SKIP
                record.response = "Skipping this subtask due to high severity."
                await self._cancel_child(child_id, reason="High-severity skip")
                if entry:
                    self.ledger.mark_cancelled(child_id)

        elif severity == EscalationSeverity.MEDIUM:
            # Medium: provide guidance
            if self.llm_call and self._can_afford_guidance():
                record.strategy = EscalationStrategy.GUIDE
                record.response = await self._generate_guidance(
                    reason, context, subtask_id,
                )
            else:
                record.strategy = EscalationStrategy.GUIDE
                record.response = (
                    "Proceed with your best judgment. "
                    "Focus on what you can accomplish with available data."
                )

        else:
            # Low severity: acknowledge and continue
            record.strategy = EscalationStrategy.GUIDE
            record.response = "Acknowledged. Continue with current approach."

        record.resolved = True
        self.escalations.append(record)

        logger.info(
            f"Governor: Escalation from {child_id} "
            f"(severity={severity.value}): {record.strategy.value} "
            f"  {record.response[:80]}"
        )

        return record

    async def _generate_guidance(
        self,
        reason: str,
        context: str,
        subtask_id: str,
    ) -> str:
        """Use LLM to generate context-aware guidance for escalation."""
        if not self.llm_call:
            return "Proceed with your best judgment."

        try:
            response = await self.llm_call(
                system_prompt=(
                    "You are a manager providing guidance to a subordinate "
                    "who is stuck. Be concise, specific, and actionable. "
                    "Suggest concrete next steps."
                ),
                user_prompt=(
                    f"Subtask: {subtask_id}\n"
                    f"Issue: {reason}\n"
                    f"Context: {context[:500]}\n\n"
                    "Provide guidance (2-3 sentences)."
                ),
            )
            return response if isinstance(response, str) else str(response)

        except Exception as e:
            logger.warning(f"Guidance generation failed: {e}")
            return "Proceed with your best judgment."

    #   Child Management  

    async def _cancel_child(self, child_id: str, reason: str = "") -> None:
        """Send a CANCEL message to a child via the message bus."""
        try:
            await self._bus.send_to_child(
                parent_id=self.parent_cell_id,
                child_id=child_id,
                channel=MessageChannel.CANCEL,
                content=reason or "Cancelled by resource governor",
                priority=MessagePriority.HIGH,
            )
            logger.info(f"Governor: Cancelled child {child_id}: {reason}")
        except Exception as e:
            logger.warning(f"Failed to cancel child {child_id}: {e}")

    def _can_afford_guidance(self) -> bool:
        """Can we afford the LLM cost of generating guidance?"""
        remaining = self.ledger.total_budget - self.ledger.total_consumed
        return remaining > 500  # ~300 tokens for guidance + margin

    #   Telemetry  

    def get_telemetry(self) -> dict[str, Any]:
        """
        Comprehensive execution telemetry.

        Returns:
            Dict with budget, timing, escalation, and action metrics.
        """
        return {
            "budget": self.ledger.to_summary(),
            "governance_cycles": self._governance_cycles,
            "escalations": {
                "total": len(self.escalations),
                "by_severity": {
                    s.value: sum(
                        1 for e in self.escalations if e.severity == s
                    )
                    for s in EscalationSeverity
                },
                "by_strategy": {
                    s.value: sum(
                        1 for e in self.escalations if e.strategy == s
                    )
                    for s in EscalationStrategy
                },
            },
            "actions": {
                "total": len(self._actions_taken),
                "by_type": _count_by_key(
                    self._actions_taken, "type",
                ),
            },
            "children": {
                child_id: {
                    "subtask_id": entry.subtask_id,
                    "status": entry.status,
                    "allocated": entry.allocated,
                    "consumed": entry.consumed,
                    "utilization": f"{entry.utilization:.0%}",
                    "elapsed_ms": f"{entry.elapsed_ms:.0f}",
                }
                for child_id, entry in self.ledger.entries.items()
            },
        }


# ============================================================================
# Execution Guard   Wraps the Full Cell Lifecycle
# ============================================================================


class ExecutionGuard:
    """
    Wraps a kernel cell's execution with governance controls.

    Provides:
    - Pre-execution budget validation
    - Mid-execution health checks
    - Post-execution audit trail
    - Timeout enforcement with graceful degradation

    Usage::

        guard = ExecutionGuard(
            cell_id="analyst-42",
            budget_max=10000,
            budget_remaining=8000,
            max_execution_ms=60000,
        )

        # Check before executing
        if guard.can_execute():
            async with guard:
                result = await cell.process(envelope)

        # Post-execution audit
        audit = guard.get_audit()
    """

    def __init__(
        self,
        cell_id: str,
        budget_max: int = 10_000,
        budget_remaining: int = 10_000,
        max_execution_ms: float = 60_000,
        depth: int = 0,
        max_depth: int = 5,
    ) -> None:
        self.cell_id = cell_id
        self.budget_max = budget_max
        self.budget_remaining = budget_remaining
        self.max_execution_ms = max_execution_ms
        self.depth = depth
        self.max_depth = max_depth

        self._started_at: datetime | None = None
        self._completed_at: datetime | None = None
        self._status: str = "pending"
        self._error: str | None = None
        self._warnings: list[str] = []

    def can_execute(self) -> bool:
        """Pre-flight check: is it safe to execute?"""
        if self.budget_remaining < 500:
            self._warnings.append(
                f"Budget too low: {self.budget_remaining} tokens"
            )
            return False

        if self.depth >= self.max_depth:
            self._warnings.append(
                f"Depth limit reached: {self.depth}/{self.max_depth}"
            )
            return False

        return True

    async def __aenter__(self) -> ExecutionGuard:
        """Start execution tracking."""
        self._started_at = datetime.utcnow()
        self._status = "running"
        return self

    async def __aexit__(
        self,
        exc_type: type | None,
        exc_val: Exception | None,
        exc_tb: Any | None,
    ) -> bool:
        """Complete execution tracking."""
        self._completed_at = datetime.utcnow()

        if exc_type is not None:
            self._status = "failed"
            self._error = str(exc_val)
            logger.error(
                f"ExecutionGuard [{self.cell_id}]: "
                f"Failed after {self.elapsed_ms:.0f}ms   {exc_val}"
            )
            return False  # Don't suppress the exception

        self._status = "completed"

        # Post-execution warnings
        if self.elapsed_ms > self.max_execution_ms:
            self._warnings.append(
                f"Exceeded time limit: {self.elapsed_ms:.0f}ms "
                f"> {self.max_execution_ms:.0f}ms"
            )

        return False

    @property
    def elapsed_ms(self) -> float:
        """Milliseconds since execution started."""
        if not self._started_at:
            return 0.0
        end = self._completed_at or datetime.utcnow()
        return (end - self._started_at).total_seconds() * 1000

    def get_audit(self) -> dict[str, Any]:
        """Post-execution audit record."""
        return {
            "cell_id": self.cell_id,
            "status": self._status,
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "completed_at": self._completed_at.isoformat() if self._completed_at else None,
            "elapsed_ms": self.elapsed_ms,
            "budget_max": self.budget_max,
            "budget_remaining": self.budget_remaining,
            "depth": self.depth,
            "warnings": self._warnings,
            "error": self._error,
        }


# ============================================================================
# Helpers
# ============================================================================


def _count_by_key(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    """Count occurrences of each value for a given key."""
    counts: dict[str, int] = {}
    for item in items:
        val = str(item.get(key, "unknown"))
        counts[val] = counts.get(val, 0) + 1
    return counts
