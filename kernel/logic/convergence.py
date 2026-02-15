"""
Convergence Detector   Determines When Recursive Self-Healing Should Stop.

Provides budget-aware, progress-tracking convergence detection for the
recursive healing loop. Prevents infinite loops via hard limits and
detects diminishing returns to stop early when further healing isn't
productive.

Version: 1.0.0   Part of Kernel Recursion (Phase 4)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from shared.logging import get_logger

from kernel.memory.error_journal import ErrorJournal

logger = get_logger(__name__)


# ============================================================================
# Data Structures
# ============================================================================


@dataclass
class IterationSnapshot:
    """Record of a single healing iteration's outcome."""

    iteration: int
    unresolved_count: int
    fixed_count: int
    cascaded_count: int
    tokens_consumed: int
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ConvergenceDecision:
    """Whether to continue healing and why."""

    continue_healing: bool
    reason: str
    detail: str = ""


# ============================================================================
# Convergence Detector
# ============================================================================


class ConvergenceDetector:
    """
    Determines when recursive self-healing should stop.

    Checks multiple termination conditions:
    1. **Full convergence**   no more unresolved errors
    2. **Budget exhaustion**   not enough tokens for another iteration
    3. **Max iterations**   hard cap on healing rounds
    4. **Max cascade depth**   fix chains too deep
    5. **Diminishing returns**   improvement rate below threshold
    6. **Error explosion**   fixes introducing too many new errors

    Usage::

        detector = ConvergenceDetector(max_iterations=3)

        while True:
            decision = detector.should_continue(journal, budget_remaining=5000)
            if not decision.continue_healing:
                break

            # ... perform healing iteration ...

            detector.record_iteration(IterationSnapshot(...))
    """

    def __init__(
        self,
        max_iterations: int = 5,
        max_cascade_depth: int = 3,
        diminishing_returns_threshold: float = 0.1,
        max_new_errors_per_iteration: int = 5,
        min_budget_for_heal: int = 1000,
    ) -> None:
        self.max_iterations = max_iterations
        self.max_cascade_depth = max_cascade_depth
        self.diminishing_returns_threshold = diminishing_returns_threshold
        self.max_new_errors_per_iteration = max_new_errors_per_iteration
        self.min_budget_for_heal = min_budget_for_heal

        self._history: list[IterationSnapshot] = []

    def should_continue(
        self,
        journal: ErrorJournal,
        budget_remaining: int,
    ) -> ConvergenceDecision:
        """Decide whether another healing iteration is warranted."""

        # 1. Full convergence   no more issues
        if journal.get_unresolved_count() == 0:
            return ConvergenceDecision(
                continue_healing=False,
                reason="fully_converged",
            )

        # 2. Budget exhaustion
        if budget_remaining < self.min_budget_for_heal:
            return ConvergenceDecision(
                continue_healing=False,
                reason="budget_exhausted",
                detail=f"Remaining {budget_remaining} < min {self.min_budget_for_heal}",
            )

        # 3. Max iterations
        if len(self._history) >= self.max_iterations:
            return ConvergenceDecision(
                continue_healing=False,
                reason="max_iterations",
                detail=f"Hit {self.max_iterations} iteration limit",
            )

        # 4. Cascade too deep
        if journal.max_cascade_depth() >= self.max_cascade_depth:
            return ConvergenceDecision(
                continue_healing=False,
                reason="cascade_too_deep",
                detail=f"Cascade depth {journal.max_cascade_depth()} >= {self.max_cascade_depth}",
            )

        # 5. Diminishing returns
        if len(self._history) >= 2:
            prev = self._history[-2]
            curr = self._history[-1]

            if prev.unresolved_count > 0:
                improvement = (
                    prev.unresolved_count - curr.unresolved_count
                ) / prev.unresolved_count
            else:
                improvement = 0.0

            if improvement < self.diminishing_returns_threshold:
                return ConvergenceDecision(
                    continue_healing=False,
                    reason="diminishing_returns",
                    detail=f"Only {improvement:.0%} improvement in last iteration",
                )

        # 6. Error explosion   last iteration created too many new errors
        if self._history:
            last = self._history[-1]
            if last.cascaded_count > self.max_new_errors_per_iteration:
                return ConvergenceDecision(
                    continue_healing=False,
                    reason="error_explosion",
                    detail=(
                        f"Last iteration introduced {last.cascaded_count} new errors "
                        f"(max {self.max_new_errors_per_iteration})"
                    ),
                )

        # All checks passed   continue healing
        return ConvergenceDecision(
            continue_healing=True,
            reason="unresolved_errors_remain",
            detail=f"{journal.get_unresolved_count()} unresolved errors",
        )

    def record_iteration(self, snapshot: IterationSnapshot) -> None:
        """Record the outcome of a healing iteration."""
        self._history.append(snapshot)
        logger.info(
            f"HealIteration {snapshot.iteration}: "
            f"fixed={snapshot.fixed_count}, "
            f"cascaded={snapshot.cascaded_count}, "
            f"remaining={snapshot.unresolved_count}, "
            f"tokens={snapshot.tokens_consumed}"
        )

    @property
    def iterations_completed(self) -> int:
        """Number of healing iterations completed."""
        return len(self._history)

    @property
    def history(self) -> list[IterationSnapshot]:
        """Full iteration history."""
        return list(self._history)

    def to_dict(self) -> dict[str, Any]:
        """Serialise detector state."""
        return {
            "iterations_completed": len(self._history),
            "max_iterations": self.max_iterations,
            "history": [
                {
                    "iteration": s.iteration,
                    "unresolved": s.unresolved_count,
                    "fixed": s.fixed_count,
                    "cascaded": s.cascaded_count,
                    "tokens": s.tokens_consumed,
                }
                for s in self._history
            ],
        }
