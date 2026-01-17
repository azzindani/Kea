"""
Tests for Supervisor Layer.
"""

import pytest
import asyncio


class TestQualityCheck:
    """Tests for quality check results."""
    
    def test_check_result(self):
        """Test quality check creation."""
        from services.orchestrator.core.supervisor import QualityCheck, CheckResult
        
        check = QualityCheck(
            name="format_check",
            result=CheckResult.PASS,
            message="All formatting correct",
            score=0.95,
        )
        
        assert check.name == "format_check"
        assert check.result == CheckResult.PASS
        assert check.score == 0.95
        
        print("\n✅ QualityCheck created")


class TestReviewResult:
    """Tests for review results."""
    
    def test_review_summary(self):
        """Test review summary generation."""
        from services.orchestrator.core.supervisor import (
            ReviewResult, QualityCheck, CheckResult
        )
        
        result = ReviewResult(
            work_id="work_123",
            passed=True,
            checks=[
                QualityCheck("format", CheckResult.PASS, score=1.0),
                QualityCheck("facts", CheckResult.PASS, score=0.9),
            ],
            overall_score=0.95,
            feedback="All checks passed",
        )
        
        summary = result.summary
        
        assert "PASSED" in summary
        assert "95" in summary
        
        print(f"\n✅ Review summary: {summary}")


class TestQualityGate:
    """Tests for QualityGate."""
    
    @pytest.mark.asyncio
    async def test_add_checker(self):
        """Test adding quality checkers."""
        from services.orchestrator.core.supervisor import QualityGate, QualityCheck, CheckResult
        
        gate = QualityGate(threshold=0.8)
        
        async def always_pass(output):
            return QualityCheck("always_pass", CheckResult.PASS, score=1.0)
        
        gate.add_checker("test", always_pass)
        
        result = await gate.validate("work_1", {"data": "test"})
        
        assert result.passed is True
        assert result.overall_score == 1.0
        
        print("\n✅ Checker added and validated")
    
    @pytest.mark.asyncio
    async def test_threshold_enforcement(self):
        """Test threshold enforcement."""
        from services.orchestrator.core.supervisor import QualityGate, QualityCheck, CheckResult
        
        gate = QualityGate(threshold=0.8)
        
        async def partial_pass(output):
            return QualityCheck("partial", CheckResult.WARN, score=0.7)
        
        gate.add_checker("partial", partial_pass)
        
        result = await gate.validate("work_2", {})
        
        assert result.passed is False  # 0.7 < 0.8 threshold
        assert result.overall_score == 0.7
        
        print("\n✅ Threshold enforced correctly")
    
    @pytest.mark.asyncio
    async def test_multiple_checkers(self):
        """Test multiple quality checkers."""
        from services.orchestrator.core.supervisor import QualityGate, QualityCheck, CheckResult
        
        gate = QualityGate(threshold=0.6)
        
        async def check_format(output):
            return QualityCheck("format", CheckResult.PASS, score=1.0)
        
        async def check_facts(output):
            return QualityCheck("facts", CheckResult.WARN, score=0.5)
        
        gate.add_checker("format", check_format)
        gate.add_checker("facts", check_facts)
        
        result = await gate.validate("work_3", {})
        
        # Average: (1.0 + 0.5) / 2 = 0.75 > 0.6 threshold
        assert result.passed is True
        assert len(result.checks) == 2
        
        print(f"\n✅ Multiple checkers: {result.overall_score:.2f}")


class TestSupervisor:
    """Tests for Supervisor."""
    
    def test_create_supervisor(self):
        """Test supervisor creation."""
        from services.orchestrator.core.supervisor import Supervisor
        
        supervisor = Supervisor()
        
        assert supervisor.quality_gate is not None
        assert supervisor.pending_escalation_count == 0
        
        print("\n✅ Supervisor created")
    
    @pytest.mark.asyncio
    async def test_monitor_team(self):
        """Test team health monitoring."""
        from services.orchestrator.core.supervisor import Supervisor
        from dataclasses import dataclass
        
        @dataclass
        class MockTeam:
            team_id: str = "team_mock"
            utilization: float = 0.5
            agents: list = None
            
            def __post_init__(self):
                if self.agents is None:
                    self.agents = []
        
        supervisor = Supervisor()
        team = MockTeam(utilization=0.5)
        
        health = await supervisor.monitor_team(team)
        
        assert health.team_id == "team_mock"
        assert health.healthy is True
        assert health.utilization == 0.5
        
        print(f"\n✅ Health check: {health.healthy}")
    
    @pytest.mark.asyncio
    async def test_escalate_to_human(self):
        """Test escalation to human."""
        from services.orchestrator.core.supervisor import Supervisor, EscalationType
        
        supervisor = Supervisor()
        escalations_received = []
        
        async def on_escalation(escalation):
            escalations_received.append(escalation)
        
        supervisor.on_escalation(on_escalation)
        
        escalation_id = await supervisor.escalate_to_human(
            EscalationType.DECISION,
            source_agent="agent_123",
            context={"query": "Should we proceed?"},
            message="Need human decision on strategy",
            work_id="work_456",
        )
        
        assert escalation_id.startswith("esc_")
        assert len(escalations_received) == 1
        assert supervisor.pending_escalation_count == 1
        
        print(f"\n✅ Escalation created: {escalation_id}")
    
    @pytest.mark.asyncio
    async def test_resolve_escalation(self):
        """Test escalation resolution."""
        from services.orchestrator.core.supervisor import Supervisor, EscalationType
        
        supervisor = Supervisor()
        
        escalation_id = await supervisor.escalate_to_human(
            EscalationType.QUALITY,
            source_agent="agent_1",
            context={},
            message="Output needs review",
        )
        
        assert supervisor.pending_escalation_count == 1
        
        success = await supervisor.resolve_escalation(
            escalation_id,
            resolution="Approved with modifications"
        )
        
        assert success is True
        assert supervisor.pending_escalation_count == 0
        
        print("\n✅ Escalation resolved")
    
    @pytest.mark.asyncio
    async def test_review_output(self):
        """Test output review through quality gate."""
        from services.orchestrator.core.supervisor import Supervisor
        
        supervisor = Supervisor()
        
        # Add a simple checker
        async def simple_check(output):
            from services.orchestrator.core.supervisor import QualityCheck, CheckResult
            return QualityCheck("simple", CheckResult.PASS, score=0.9)
        
        supervisor.quality_gate.add_checker("simple", simple_check)
        
        result = await supervisor.review_output("work_789", {"result": "data"})
        
        assert result.passed is True
        
        print(f"\n✅ Review: {result.summary}")
    
    def test_singleton(self):
        """Test supervisor singleton."""
        from services.orchestrator.core.supervisor import get_supervisor
        
        sup1 = get_supervisor()
        sup2 = get_supervisor()
        
        assert sup1 is sup2
        
        print("\n✅ Supervisor singleton works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
