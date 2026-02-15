"""
Error Journal   Structured Error Tracking for Recursive Self-Healing.

Provides a persistent record of all errors encountered, diagnosis attempts,
and fixes applied within a kernel cell's lifetime. This is the foundation
that enables Claude Code-style recursive self-healing: detect   diagnose  
fix   cascade-check   repeat.

Key concepts:
- **ErrorEntry**: A single error with lifecycle (DETECTED   DIAGNOSING   FIXING   FIXED)
- **FixAttempt**: A record of one fix attempt, including any new errors it discovered
- **Causality Graph**: Tracks which errors caused which other errors (DAG)
- **Convergence**: Knows when the recursive fix chain has stabilized

Version: 0.4.0   Part of Kernel Recursion (Phase 1)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from shared.logging import get_logger

logger = get_logger(__name__)


# ============================================================================
# Enums
# ============================================================================


class ErrorSource(StrEnum):
    """Where the error originated."""

    TOOL_FAILURE = "tool_failure"
    QUALITY_GATE = "quality_gate"
    DELEGATION_FAILURE = "delegation_failure"
    VALIDATION = "validation"
    RUNTIME = "runtime"
    CASCADE = "cascade"


class ErrorSeverity(StrEnum):
    """How severe the error is."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorStatus(StrEnum):
    """Lifecycle state of an error."""

    DETECTED = "detected"
    DIAGNOSING = "diagnosing"
    FIXING = "fixing"
    FIXED = "fixed"
    WONT_FIX = "wont_fix"
    CASCADED = "cascaded"


class FixResult(StrEnum):
    """Outcome of a fix attempt."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    CASCADED = "cascaded"


# ============================================================================
# Data Structures
# ============================================================================


@dataclass
class FixAttempt:
    """A single attempt to fix an error."""

    attempt_number: int
    strategy: str
    result: FixResult = FixResult.FAILED
    new_errors_discovered: list[str] = field(default_factory=list)
    tokens_consumed: int = 0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ErrorEntry:
    """A single error encountered during execution."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Classification
    source: ErrorSource = ErrorSource.RUNTIME
    error_type: str = ""
    message: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    severity: ErrorSeverity = ErrorSeverity.MEDIUM

    # Diagnosis
    root_cause: str | None = None
    related_errors: list[str] = field(default_factory=list)

    # Fix tracking
    fix_attempts: list[FixAttempt] = field(default_factory=list)
    status: ErrorStatus = ErrorStatus.DETECTED

    # Complexity estimate for fix planning
    estimated_complexity: str = "moderate"


# ============================================================================
# Error Journal
# ============================================================================


class ErrorJournal:
    """
    Persistent error tracking across recursive healing iterations.

    Maintains a DAG of error causality (which fixes caused which errors)
    and provides convergence detection for the recursive healing loop.

    Usage::

        journal = ErrorJournal()

        # Record an error
        err_id = journal.record(ErrorEntry(
            source=ErrorSource.TOOL_FAILURE,
            message="web_search failed: timeout",
            context={"tool": "web_search", "args": {"q": "test"}},
            severity=ErrorSeverity.MEDIUM,
        ))

        # Diagnose
        journal.diagnose(err_id, "MCP Host unreachable on port 8002")

        # Record a fix attempt
        journal.record_fix(err_id, FixAttempt(
            attempt_number=1,
            strategy="Retry with increased timeout",
            result=FixResult.SUCCESS,
        ))

        # Check convergence
        if journal.is_converged():
            print("All errors resolved!")
    """

    def __init__(self) -> None:
        self._entries: dict[str, ErrorEntry] = {}
        self._fix_graph: dict[str, list[str]] = {}  # error_id   [caused_error_ids]
        self._iteration: int = 0

    #   Recording  

    def record(self, error: ErrorEntry) -> str:
        """Record a new error. Returns the error ID."""
        self._entries[error.id] = error
        self._fix_graph.setdefault(error.id, [])
        logger.debug(
            f"ErrorJournal: recorded {error.source.value} error "
            f"({error.severity.value}): {error.message[:80]}"
        )
        return error.id

    def record_from_tool_failure(
        self,
        tool_name: str,
        error_message: str,
        arguments: dict[str, Any] | None = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    ) -> str:
        """Convenience: record a tool execution failure."""
        entry = ErrorEntry(
            source=ErrorSource.TOOL_FAILURE,
            error_type=f"tool_{tool_name}_failure",
            message=error_message,
            context={
                "tool": tool_name,
                "arguments": arguments or {},
            },
            severity=severity,
            estimated_complexity="simple",
        )
        return self.record(entry)

    def record_from_quality_gate(
        self,
        failures: list[str],
        score_card_summary: str = "",
    ) -> str:
        """Convenience: record a quality gate failure."""
        entry = ErrorEntry(
            source=ErrorSource.QUALITY_GATE,
            error_type="quality_gate_failure",
            message=f"Quality gate failed: {', '.join(failures)}",
            context={
                "failures": failures,
                "score_card": score_card_summary,
            },
            severity=ErrorSeverity.HIGH,
            estimated_complexity="moderate",
        )
        return self.record(entry)

    #   Diagnosis  

    def diagnose(self, error_id: str, root_cause: str) -> None:
        """Set the diagnosed root cause for an error."""
        if error_id in self._entries:
            self._entries[error_id].root_cause = root_cause
            self._entries[error_id].status = ErrorStatus.DIAGNOSING
            logger.debug(f"ErrorJournal: diagnosed {error_id}: {root_cause[:80]}")

    #   Fix Tracking  

    def record_fix(self, error_id: str, attempt: FixAttempt) -> None:
        """Record a fix attempt for an error."""
        if error_id not in self._entries:
            return

        entry = self._entries[error_id]
        entry.fix_attempts.append(attempt)

        if attempt.result == FixResult.SUCCESS:
            entry.status = ErrorStatus.FIXED
        elif attempt.result == FixResult.CASCADED:
            entry.status = ErrorStatus.CASCADED
        elif attempt.result == FixResult.PARTIAL:
            entry.status = ErrorStatus.FIXING

        # Link cascade errors
        for new_err_id in attempt.new_errors_discovered:
            self.link_cascade(error_id, new_err_id)

    def mark_wont_fix(self, error_id: str, reason: str = "") -> None:
        """Mark an error as won't-fix (e.g., budget exhausted)."""
        if error_id in self._entries:
            self._entries[error_id].status = ErrorStatus.WONT_FIX
            if reason:
                self._entries[error_id].context["wont_fix_reason"] = reason

    #   Causality Graph  

    def link_cascade(self, parent_error_id: str, child_error_id: str) -> None:
        """Link a cascade: fixing parent_error caused child_error."""
        self._fix_graph.setdefault(parent_error_id, [])
        if child_error_id not in self._fix_graph[parent_error_id]:
            self._fix_graph[parent_error_id].append(child_error_id)

        # Mark the child as cascade-sourced
        if child_error_id in self._entries:
            self._entries[child_error_id].related_errors.append(parent_error_id)

    def get_cascade_chain(self, error_id: str) -> list[ErrorEntry]:
        """Get all errors in the cascade chain starting from error_id."""
        chain: list[ErrorEntry] = []
        visited: set[str] = set()

        def _walk(eid: str) -> None:
            if eid in visited:
                return
            visited.add(eid)
            if eid in self._entries:
                chain.append(self._entries[eid])
            for child_id in self._fix_graph.get(eid, []):
                _walk(child_id)

        _walk(error_id)
        return chain

    def max_cascade_depth(self) -> int:
        """Get the maximum depth of the causality DAG."""
        if not self._fix_graph:
            return 0

        # Find roots (errors not caused by any other error)
        all_children: set[str] = set()
        for children in self._fix_graph.values():
            all_children.update(children)
        roots = [eid for eid in self._entries if eid not in all_children]

        if not roots:
            return 0

        max_depth = 0

        def _depth(eid: str, current: int) -> None:
            nonlocal max_depth
            max_depth = max(max_depth, current)
            for child_id in self._fix_graph.get(eid, []):
                _depth(child_id, current + 1)

        for root in roots:
            _depth(root, 0)

        return max_depth

    #   Queries  

    def get_unresolved(self) -> list[ErrorEntry]:
        """Get all errors that haven't been fixed or dismissed."""
        return [
            e
            for e in self._entries.values()
            if e.status in (ErrorStatus.DETECTED, ErrorStatus.DIAGNOSING, ErrorStatus.FIXING)
        ]

    def get_unresolved_count(self) -> int:
        """Count of unresolved errors."""
        return len(self.get_unresolved())

    def count_by_status(self, status: ErrorStatus) -> int:
        """Count errors in a given status."""
        return sum(1 for e in self._entries.values() if e.status == status)

    def get_all(self) -> list[ErrorEntry]:
        """Get all recorded errors."""
        return list(self._entries.values())

    def get_entry(self, error_id: str) -> ErrorEntry | None:
        """Get a specific error entry."""
        return self._entries.get(error_id)

    #   Convergence  

    def is_converged(self) -> bool:
        """True if there are no unresolved errors."""
        return self.get_unresolved_count() == 0

    #   Iteration Tracking  

    def advance_iteration(self) -> int:
        """Advance the iteration counter."""
        self._iteration += 1
        return self._iteration

    @property
    def iteration(self) -> int:
        """Current iteration number."""
        return self._iteration

    #   Serialisation  

    def compress_for_llm(self, max_chars: int = 2000) -> str:
        """
        Compress the error journal into an LLM-ingestible summary.

        Prioritises unresolved errors, then recently fixed, then dismissed.
        """
        if not self._entries:
            return ""

        sections: list[str] = []
        budget = max_chars

        # Unresolved errors (highest priority)
        unresolved = self.get_unresolved()
        if unresolved:
            lines = []
            for err in unresolved[:5]:
                cause = f" (cause: {err.root_cause[:60]})" if err.root_cause else ""
                lines.append(
                    f"- [{err.severity.value}] {err.source.value}: {err.message[:100]}{cause}"
                )
            section = f"UNRESOLVED ERRORS ({len(unresolved)}):\n" + "\n".join(lines)
            sections.append(section)
            budget -= len(section)

        # Recently fixed
        fixed = [e for e in self._entries.values() if e.status == ErrorStatus.FIXED]
        if fixed and budget > 200:
            lines = []
            for err in fixed[-3:]:
                strategy = ""
                if err.fix_attempts:
                    strategy = f"   fix: {err.fix_attempts[-1].strategy[:60]}"
                lines.append(f"- {err.message[:80]}{strategy}")
            section = f"RECENTLY FIXED ({len(fixed)}):\n" + "\n".join(lines)
            sections.append(section)
            budget -= len(section)

        # Cascade summary
        max_depth = self.max_cascade_depth()
        if max_depth > 0 and budget > 100:
            section = f"CASCADE DEPTH: {max_depth} (max)"
            sections.append(section)

        return "\n\n".join(sections)

    def to_dict(self) -> dict[str, Any]:
        """Serialise journal state to a dictionary."""
        return {
            "total_errors": len(self._entries),
            "unresolved": self.get_unresolved_count(),
            "fixed": self.count_by_status(ErrorStatus.FIXED),
            "wont_fix": self.count_by_status(ErrorStatus.WONT_FIX),
            "cascade_depth": self.max_cascade_depth(),
            "iteration": self._iteration,
        }
