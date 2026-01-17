"""
v3.0 Enterprise Simulation Test.

Simulates the full enterprise workflow:
- Organization hierarchy
- Work unit management
- Inter-agent messaging
- Supervisor oversight
"""

import pytest
import asyncio
from dataclasses import dataclass


class TestEnterpriseOrganizationSimulation:
    """Simulate organization hierarchy operations."""
    
    def test_create_full_hierarchy(self):
        """Test creating complete org hierarchy."""
        from services.orchestrator.core.organization import (
            Organization, Domain, Role, RoleType
        )
        
        org = Organization()
        
        # Create 3 departments
        research = org.create_department("Research", Domain.RESEARCH)
        finance = org.create_department("Finance", Domain.FINANCE)
        legal = org.create_department("Legal", Domain.LEGAL)
        
        # Add teams to each
        research.add_team("Market Analysis", max_agents=10)
        research.add_team("Competitor Intel", max_agents=5)
        finance.add_team("Quantitative", max_agents=8)
        legal.add_team("Compliance", max_agents=3)
        
        # Add agents
        analyst = Role("Analyst", RoleType.ANALYST, "Analyze data")
        for team in research.teams:
            for _ in range(3):
                team.add_agent(analyst)
        
        stats = org.stats
        
        assert stats["departments"] == 3
        assert stats["total_agents"] >= 6
        
        print(f"\n✅ Created organization: {stats}")
    
    def test_department_domain_routing(self):
        """Test routing by domain."""
        from services.orchestrator.core.organization import (
            Organization, Domain
        )
        
        org = Organization()
        org.create_department("R&D", Domain.RESEARCH)
        org.create_department("FP&A", Domain.FINANCE)
        
        # Route by domain
        research_dept = org.get_department_by_domain(Domain.RESEARCH)
        finance_dept = org.get_department_by_domain(Domain.FINANCE)
        
        assert research_dept is not None
        assert finance_dept is not None
        assert research_dept.name == "R&D"
        
        print("\n✅ Domain routing works")


class TestWorkBoardSimulation:
    """Simulate work board operations."""
    
    def test_work_queue_priority(self):
        """Test priority-based work queue."""
        from services.orchestrator.core.work_unit import (
            WorkBoard, WorkUnit, WorkType, Priority
        )
        
        board = WorkBoard()
        
        # Add work in reverse priority order
        board.add(WorkUnit.create("Low task", WorkType.RESEARCH, priority=Priority.LOW))
        board.add(WorkUnit.create("Normal task", WorkType.ANALYSIS, priority=Priority.NORMAL))
        board.add(WorkUnit.create("Critical task", WorkType.DECISION, priority=Priority.CRITICAL))
        board.add(WorkUnit.create("High task", WorkType.SYNTHESIS, priority=Priority.HIGH))
        
        # Get next should return by priority
        next_work = board.get_next_pending()
        
        assert next_work.priority == Priority.CRITICAL
        
        print("\n✅ Priority queue works correctly")
    
    def test_work_dependency_chain(self):
        """Test work with dependencies."""
        from services.orchestrator.core.work_unit import (
            WorkBoard, WorkUnit, WorkType, WorkStatus
        )
        
        board = WorkBoard()
        
        # Create dependency chain: A -> B -> C
        work_a = WorkUnit.create("Task A", WorkType.RESEARCH)
        work_b = WorkUnit.create("Task B", WorkType.ANALYSIS)
        work_b.dependencies = [work_a.work_id]
        work_c = WorkUnit.create("Task C", WorkType.SYNTHESIS)
        work_c.dependencies = [work_b.work_id]
        
        board.add(work_a)
        board.add(work_b)
        board.add(work_c)
        
        # Block B and C
        work_b.block(work_a.work_id)
        work_c.block(work_b.work_id)
        
        # Complete A should unblock B
        board.complete(work_a.work_id, result={"data": "A done"})
        
        # B should now be pending
        assert work_b.status == WorkStatus.PENDING
        
        print("\n✅ Dependency chain works")
    
    def test_board_statistics(self):
        """Test board statistics tracking."""
        from services.orchestrator.core.work_unit import (
            WorkBoard, WorkUnit, WorkType, Priority
        )
        
        board = WorkBoard()
        
        # Add various work
        for i in range(5):
            board.add(WorkUnit.create(f"Task {i}", WorkType.RESEARCH, priority=Priority.NORMAL))
        
        for i in range(3):
            work = WorkUnit.create(f"Done {i}", WorkType.ANALYSIS)
            work.complete()
            board.add(work)
        
        stats = board.stats
        
        assert stats["total"] == 8
        assert stats["by_status"]["pending"] == 5
        assert stats["by_status"]["completed"] == 3
        
        print(f"\n✅ Board stats: {stats}")


class TestMessagingSimulation:
    """Simulate inter-agent messaging."""
    
    @pytest.mark.asyncio
    async def test_multi_agent_messaging(self):
        """Test messaging between multiple agents."""
        from services.orchestrator.core.messaging import (
            MessageBus, Message, MessageType
        )
        
        bus = MessageBus()
        received = {"a": [], "b": [], "c": []}
        
        async def handler_a(msg):
            received["a"].append(msg.content)
        
        async def handler_b(msg):
            received["b"].append(msg.content)
        
        async def handler_c(msg):
            received["c"].append(msg.content)
        
        await bus.subscribe("agent_a", handler_a)
        await bus.subscribe("agent_b", handler_b)
        await bus.subscribe("agent_c", handler_c)
        
        # A sends to B
        await bus.send(Message.create("agent_a", "agent_b", MessageType.INFO, {"msg": "hello B"}))
        
        # A broadcasts
        await bus.broadcast("agent_a", {"broadcast": "all hands"})
        
        assert len(received["b"]) >= 1
        
        print(f"\n✅ Multi-agent messaging: {bus.stats}")
    
    @pytest.mark.asyncio
    async def test_request_response_flow(self):
        """Test request-response pattern."""
        from services.orchestrator.core.messaging import (
            MessageBus, Message, MessageType
        )
        
        bus = MessageBus()
        
        async def responder(msg):
            if msg.message_type == MessageType.REQUEST:
                response = msg.create_response({"answer": msg.content.get("query", "unknown")})
                await bus.send(response)
        
        await bus.subscribe("worker", responder)
        await bus.subscribe("requester", lambda m: None)
        
        response = await bus.request(
            "requester", "worker",
            {"query": "What is 2+2?"},
            timeout=5.0
        )
        
        assert response is not None
        assert response.content["answer"] == "What is 2+2?"
        
        print("\n✅ Request-response flow works")


class TestSupervisorSimulation:
    """Simulate supervisor oversight."""
    
    @pytest.mark.asyncio
    async def test_quality_gate_pipeline(self):
        """Test quality gate with multiple checkers."""
        from services.orchestrator.core.supervisor import (
            Supervisor, QualityCheck, CheckResult
        )
        
        supervisor = Supervisor()
        
        # Add multiple quality checkers
        async def check_length(output):
            is_long = len(str(output)) > 10
            return QualityCheck("length", CheckResult.PASS if is_long else CheckResult.FAIL, score=0.9 if is_long else 0.3)
        
        async def check_format(output):
            has_data = isinstance(output, dict)
            return QualityCheck("format", CheckResult.PASS if has_data else CheckResult.FAIL, score=0.8 if has_data else 0.2)
        
        async def check_completeness(output):
            has_result = output.get("result") is not None if isinstance(output, dict) else False
            return QualityCheck("completeness", CheckResult.PASS if has_result else CheckResult.WARN, score=0.7)
        
        supervisor.quality_gate.add_checker("length", check_length)
        supervisor.quality_gate.add_checker("format", check_format)
        supervisor.quality_gate.add_checker("completeness", check_completeness)
        
        # Good output
        good_output = {"result": "Tesla revenue is $81B", "source": "10-K"}
        result = await supervisor.review_output("work_1", good_output)
        
        assert result.passed is True
        assert len(result.checks) == 3
        
        print(f"\n✅ Quality gate: {result.summary}")
    
    @pytest.mark.asyncio
    async def test_escalation_chain(self):
        """Test escalation to human."""
        from services.orchestrator.core.supervisor import (
            Supervisor, EscalationType
        )
        
        supervisor = Supervisor()
        escalations = []
        
        async def on_escalation(esc):
            escalations.append(esc)
        
        supervisor.on_escalation(on_escalation)
        
        # Escalate decision
        esc1 = await supervisor.escalate_to_human(
            EscalationType.DECISION,
            source_agent="agent_1",
            context={"question": "Should we proceed?"},
            message="Need human input"
        )
        
        # Escalate quality issue
        esc2 = await supervisor.escalate_to_human(
            EscalationType.QUALITY,
            source_agent="agent_2",
            context={"score": 0.4},
            message="Output quality too low",
            work_id="work_123"
        )
        
        assert len(escalations) == 2
        assert supervisor.pending_escalation_count == 2
        
        # Resolve one
        await supervisor.resolve_escalation(esc1, "Proceed approved")
        
        assert supervisor.pending_escalation_count == 1
        
        print("\n✅ Escalation chain works")


class TestFullEnterpriseFlow:
    """Test complete enterprise workflow."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Simulate full workflow: org → work → message → supervise."""
        from services.orchestrator.core.organization import (
            Organization, Domain, Role, RoleType
        )
        from services.orchestrator.core.work_unit import (
            WorkBoard, WorkUnit, WorkType, Priority
        )
        from services.orchestrator.core.messaging import (
            MessageBus, Message, MessageType
        )
        from services.orchestrator.core.supervisor import (
            Supervisor, QualityCheck, CheckResult
        )
        
        # 1. Setup organization
        org = Organization()
        research = org.create_department("Research", Domain.RESEARCH)
        team = research.add_team("Analysis", max_agents=3)
        
        analyst = Role("Analyst", RoleType.ANALYST, "Analyze")
        agent = team.add_agent(analyst)
        
        # 2. Create work
        board = WorkBoard()
        work = WorkUnit.create(
            "Analyze Tesla Q4",
            WorkType.ANALYSIS,
            priority=Priority.HIGH
        )
        board.add(work)
        
        # 3. Assign work
        board.assign(work.work_id, agent.agent_id, research.dept_id)
        work.start()
        
        # 4. Set up messaging
        bus = MessageBus()
        
        async def agent_handler(msg):
            pass  # Agent processes message
        
        await bus.subscribe(agent.agent_id, agent_handler)
        
        # 5. Simulate work completion
        work.update_progress(1.0)
        result = {"revenue": "$81B", "growth": "25%"}
        
        # 6. Quality review
        supervisor = Supervisor()
        
        async def check_result(output):
            return QualityCheck("result_check", CheckResult.PASS, score=0.9)
        
        supervisor.quality_gate.add_checker("result", check_result)
        
        review = await supervisor.review_output(work.work_id, result)
        
        if review.passed:
            board.complete(work.work_id, result=result)
        
        # Verify
        assert work.result is not None
        assert org.total_agents == 1
        assert review.passed is True
        
        print("\n✅ Full enterprise workflow completed!")
        print(f"   Org: {org.stats}")
        print(f"   Work: {board.stats}")
        print(f"   Review: {review.summary}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
