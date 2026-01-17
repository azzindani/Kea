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
class QualityCheck:
    """Result of a single quality check."""
    name: str
    result: CheckResult
    message: str = ""
    score: float = 1.0  # 0-1


@dataclass
class ReviewResult:
    """Result of work review."""
    work_id: str
    passed: bool
    checks: list[QualityCheck] = field(default_factory=list)
    overall_score: float = 0.0
    feedback: str = ""
    reviewed_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def summary(self) -> str:
        """Summary of review."""
        status = "PASSED" if self.passed else "FAILED"
        return f"{status} ({self.overall_score:.1%}): {self.feedback}"


@dataclass
class HealthReport:
    """Team health report."""
    team_id: str
    healthy: bool
    utilization: float        # 0-1
    active_agents: int
    blocked_tasks: int
    error_rate: float         # Recent error rate
    avg_task_duration: float  # Seconds
    issues: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


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


# Type aliases
CheckerFunc = Callable[[Any], Awaitable[QualityCheck]]
EscalationHandler = Callable[[Escalation], Awaitable[None]]


class QualityGate:
    """
    Automated output validation.
    
    Runs multiple checkers against work output.
    
    Example:
        gate = QualityGate(threshold=0.8)
        
        # Add checkers
        gate.add_checker("format", check_format)
        gate.add_checker("facts", check_facts)
        
        # Validate output
        result = await gate.validate(work_output)
        if result.passed:
            # Accept output
        else:
            # Request revision
    """
    
    def __init__(self, threshold: float = 0.8):
        self.threshold = threshold
        self._checkers: dict[str, CheckerFunc] = {}
    
    def add_checker(self, name: str, checker: CheckerFunc) -> None:
        """Add quality checker."""
        self._checkers[name] = checker
        logger.debug(f"Added quality checker: {name}")
    
    def remove_checker(self, name: str) -> None:
        """Remove quality checker."""
        self._checkers.pop(name, None)
    
    async def validate(self, work_id: str, output: Any) -> ReviewResult:
        """
        Validate output against all checkers.
        
        Returns ReviewResult with overall score and individual check results.
        """
        checks = []
        
        for name, checker in self._checkers.items():
            try:
                result = await checker(output)
                checks.append(result)
            except Exception as e:
                checks.append(QualityCheck(
                    name=name,
                    result=CheckResult.FAIL,
                    message=f"Checker error: {e}",
                    score=0.0,
                ))
        
        # Calculate overall score
        if checks:
            overall_score = sum(c.score for c in checks) / len(checks)
        else:
            overall_score = 1.0  # No checkers = pass
        
        passed = overall_score >= self.threshold - 1e-9  # Floating point tolerance
        
        # Generate feedback
        failed_checks = [c for c in checks if c.result == CheckResult.FAIL]
        if failed_checks:
            feedback = f"Failed checks: {', '.join(c.name for c in failed_checks)}"
        elif not passed:
            feedback = f"Score {overall_score:.1%} below threshold {self.threshold:.1%}"
        else:
            feedback = "All quality checks passed"
        
        return ReviewResult(
            work_id=work_id,
            passed=passed,
            checks=checks,
            overall_score=overall_score,
            feedback=feedback,
        )


class Supervisor:
    """
    Oversees team performance and quality.
    
    Responsibilities:
    - Monitor team health
    - Review work output
    - Escalate to human when needed
    - Redistribute load
    
    Example:
        supervisor = Supervisor()
        
        # Monitor team
        health = await supervisor.monitor_team(team)
        if not health.healthy:
            await supervisor.redistribute_load(teams)
        
        # Review work
        result = await supervisor.review_output(work)
        if not result.passed:
            await supervisor.request_revision(work)
    """
    
    def __init__(self):
        self._quality_gate = QualityGate()
        self._escalation_handlers: list[EscalationHandler] = []
        self._pending_escalations: dict[str, Escalation] = {}
    
    @property
    def quality_gate(self) -> QualityGate:
        """Get quality gate."""
        return self._quality_gate
    
    def on_escalation(self, handler: EscalationHandler) -> None:
        """Register escalation handler."""
        self._escalation_handlers.append(handler)
    
    async def monitor_team(self, team: Any) -> HealthReport:
        """
        Monitor team health.
        
        Checks utilization, error rates, blocked tasks.
        """
        issues = []
        
        # Check utilization
        utilization = getattr(team, "utilization", 0.0)
        if utilization > 0.9:
            issues.append(f"High utilization: {utilization:.1%}")
        
        # Check for blocked agents
        agents = getattr(team, "agents", [])
        blocked = sum(1 for a in agents if getattr(a, "status", "") == "blocked")
        if blocked > 0:
            issues.append(f"{blocked} blocked agents")
        
        # Determine health
        healthy = len(issues) == 0 or (utilization < 0.95 and blocked == 0)
        
        return HealthReport(
            team_id=getattr(team, "team_id", "unknown"),
            healthy=healthy,
            utilization=utilization,
            active_agents=len(agents),
            blocked_tasks=blocked,
            error_rate=0.0,  # Would need metrics tracking
            avg_task_duration=0.0,  # Would need metrics tracking
            issues=issues,
        )
    
    async def review_output(self, work_id: str, output: Any) -> ReviewResult:
        """Review work output through quality gate."""
        return await self._quality_gate.validate(work_id, output)
    
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
    
    async def redistribute_load(
        self,
        from_team: Any,
        to_team: Any,
        count: int = 1,
    ) -> int:
        """
        Move tasks between teams.
        
        Returns number of tasks moved.
        """
        # Would integrate with WorkBoard to move pending tasks
        logger.info(f"Redistributing {count} tasks from {from_team} to {to_team}")
        return 0  # Placeholder
    
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
