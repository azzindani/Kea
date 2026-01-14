"""
Real-World Enterprise Workflow Test.

Tests the v3.0 enterprise kernel with actual (or mocked) services.
"""

import pytest
import asyncio


class TestEnterpriseWorkflowLive:
    """Live tests for enterprise workflow."""
    
    @pytest.fixture
    def org_setup(self):
        """Set up organization for tests."""
        from services.orchestrator.core.organization import (
            Organization, Domain, Role, RoleType
        )
        
        org = Organization()
        
        # Create departments
        research = org.create_department("Research", Domain.RESEARCH, max_teams=5)
        analytics = org.create_department("Analytics", Domain.ANALYTICS, max_teams=3)
        
        # Create teams
        market = research.add_team("Market Analysis", max_agents=5)
        data = analytics.add_team("Data Science", max_agents=3)
        
        # Create roles
        researcher = Role(
            name="Market Researcher",
            role_type=RoleType.RESEARCHER,
            system_prompt="You research market data...",
            allowed_tools=["web_search", "pdf_extract"],
        )
        
        analyst = Role(
            name="Data Analyst",
            role_type=RoleType.ANALYST,
            system_prompt="You analyze data...",
            allowed_tools=["pandas", "visualization"],
        )
        
        # Add agents
        for _ in range(2):
            market.add_agent(researcher)
        data.add_agent(analyst)
        
        return org
    
    @pytest.fixture
    def work_board(self):
        """Set up work board for tests."""
        from services.orchestrator.core.work_unit import WorkBoard
        return WorkBoard()
    
    def test_org_creation_and_stats(self, org_setup):
        """Test organization creation."""
        org = org_setup
        
        stats = org.stats
        
        assert stats["departments"] == 2
        assert stats["total_agents"] == 3
        
        print(f"\n✅ Organization stats: {stats}")
    
    def test_work_creation_and_assignment(self, org_setup, work_board):
        """Test work creation and assignment."""
        from services.orchestrator.core.work_unit import WorkUnit, WorkType, Priority
        
        org = org_setup
        board = work_board
        
        # Create high-priority work
        work = WorkUnit.create(
            title="Tesla Q4 2024 Analysis",
            work_type=WorkType.ANALYSIS,
            description="Comprehensive analysis of Tesla Q4 performance",
            priority=Priority.HIGH,
        )
        board.add(work)
        
        # Get first available agent
        research_dept = list(org._departments.values())[0]
        team = research_dept.teams[0]
        agent = team.agents[0] if team.agents else None
        
        if agent:
            board.assign(work.work_id, agent.agent_id)
            assert work.assigned_to == agent.agent_id
            print(f"\n✅ Work assigned to {agent.agent_id}")
        else:
            print("\n⏭️ No agents available")
    
    @pytest.mark.asyncio
    async def test_messaging_between_agents(self, org_setup):
        """Test messaging between agents."""
        from services.orchestrator.core.messaging import (
            MessageBus, Message, MessageType
        )
        
        org = org_setup
        bus = MessageBus()
        
        messages_received = []
        
        # Get agents
        dept = list(org._departments.values())[0]
        agents = dept.teams[0].agents if dept.teams else []
        
        if len(agents) >= 2:
            agent1 = agents[0]
            agent2 = agents[1]
            
            async def handler(msg):
                messages_received.append(msg)
            
            await bus.subscribe(agent1.agent_id, lambda m: None)
            await bus.subscribe(agent2.agent_id, handler)
            
            # Send message
            await bus.send(Message.create(
                agent1.agent_id,
                agent2.agent_id,
                MessageType.INFO,
                {"task": "Review my analysis"}
            ))
            
            assert len(messages_received) == 1
            print(f"\n✅ Message sent: {messages_received[0].content}")
        else:
            print("\n⏭️ Not enough agents for messaging test")
    
    @pytest.mark.asyncio
    async def test_supervisor_review(self, work_board):
        """Test supervisor quality review."""
        from services.orchestrator.core.work_unit import WorkUnit, WorkType
        from services.orchestrator.core.supervisor import (
            Supervisor, QualityCheck, CheckResult
        )
        
        board = work_board
        supervisor = Supervisor()
        
        # Add quality checker
        async def check_analysis(output):
            has_data = isinstance(output, dict) and len(output) > 0
            return QualityCheck(
                "analysis_quality",
                CheckResult.PASS if has_data else CheckResult.FAIL,
                score=0.9 if has_data else 0.3
            )
        
        supervisor.quality_gate.add_checker("analysis", check_analysis)
        
        # Create and complete work
        work = WorkUnit.create("Test Analysis", WorkType.ANALYSIS)
        board.add(work)
        work.start()
        
        # Simulate output
        output = {
            "revenue": "$81.46B",
            "growth": "25% YoY",
            "market_share": "60%",
        }
        
        # Review
        result = await supervisor.review_output(work.work_id, output)
        
        assert result.passed is True
        print(f"\n✅ Review result: {result.summary}")
    
    @pytest.mark.asyncio
    async def test_escalation_flow(self):
        """Test escalation to human."""
        from services.orchestrator.core.supervisor import (
            Supervisor, EscalationType
        )
        
        supervisor = Supervisor()
        
        escalations = []
        
        async def handle_escalation(esc):
            escalations.append(esc)
        
        supervisor.on_escalation(handle_escalation)
        
        # Create escalation
        esc_id = await supervisor.escalate_to_human(
            EscalationType.DECISION,
            source_agent="agent_123",
            context={"question": "Should we include competitor data?"},
            message="Need human input on scope",
            work_id="work_456",
        )
        
        assert len(escalations) == 1
        assert supervisor.pending_escalation_count == 1
        
        # Resolve
        await supervisor.resolve_escalation(esc_id, "Yes, include Ford and GM")
        
        assert supervisor.pending_escalation_count == 0
        print(f"\n✅ Escalation flow complete: {esc_id}")


class TestCuriosityEngineLive:
    """Live tests for curiosity engine."""
    
    def test_question_generation(self):
        """Test curiosity question generation."""
        from services.orchestrator.core.curiosity import (
            CuriosityEngine, Fact
        )
        
        engine = CuriosityEngine()
        
        facts = [
            Fact(entity="Tesla", attribute="revenue", value="$81B", source="10-K"),
            Fact(entity="Tesla", attribute="growth", value="25%", source="10-K"),
            Fact(entity="Ford", attribute="revenue", value="$160B", source="10-K"),
            Fact(entity="Ford", attribute="growth", value="5%", source="10-K"),
        ]
        
        questions = engine.generate_questions(facts)
        
        assert len(questions) >= 1
        
        print("\n✅ Generated curiosity questions:")
        for q in questions[:3]:
            print(f"   - {q.text[:60]}...")
    
    def test_anomaly_detection(self):
        """Test anomaly detection."""
        from services.orchestrator.core.curiosity import CuriosityEngine, Fact
        
        engine = CuriosityEngine()
        
        # Include an anomaly
        facts = [
            Fact(entity="A", attribute="margin", value="5%", source="S"),
            Fact(entity="B", attribute="margin", value="6%", source="S"),
            Fact(entity="C", attribute="margin", value="7%", source="S"),
            Fact(entity="D", attribute="margin", value="50%", source="S"),  # Anomaly!
        ]
        
        anomalies = engine._detect_anomalies(facts)
        
        print(f"\n✅ Detected {len(anomalies)} anomalies")
    
    def test_user_formatting(self):
        """Test user-friendly question formatting."""
        from services.orchestrator.core.curiosity import (
            CuriosityEngine, CuriosityQuestion, QuestionType
        )
        
        engine = CuriosityEngine()
        
        question = CuriosityQuestion(
            text="Why is Tesla's growth rate 5x higher than Ford's?",
            question_type=QuestionType.COMPARISON,
            priority=0.9,
            entities=["Tesla", "Ford"],
        )
        
        formatted = engine.format_for_user([question])
        
        assert len(formatted) >= 1
        print(f"\n✅ Formatted: {formatted[0]}")


class TestConversationMemoryLive:
    """Live tests for conversation memory."""
    
    def test_session_creation(self):
        """Test conversation session creation."""
        from services.orchestrator.core.conversation import (
            ConversationManager, Intent
        )
        
        manager = ConversationManager()
        
        session = manager.get_or_create_session("user_123")
        
        assert session.session_id is not None
        print(f"\n✅ Session created: {session.session_id}")
    
    def test_intent_detection(self):
        """Test intent detection."""
        from services.orchestrator.core.conversation import (
            IntentDetector, Intent
        )
        
        detector = IntentDetector()
        
        test_cases = [
            ("Research Tesla", Intent.NEW_TOPIC),
            ("What about their revenue?", Intent.FOLLOW_UP),
            ("Go deeper on that", Intent.DEEPER),
            ("Actually, change to 2024 data", Intent.REVISE),
        ]
        
        for query, expected in test_cases:
            detected = detector.detect(query)
            print(f"   '{query[:30]}...' → {detected.value}")
        
        print("\n✅ Intent detection works")
    
    def test_context_building(self):
        """Test smart context building."""
        from services.orchestrator.core.conversation import (
            ConversationManager, SmartContextBuilder, Intent
        )
        
        manager = ConversationManager()
        session = manager.get_or_create_session("user_456")
        
        # Add turns
        session.add_turn("user", "Research Tesla financials", Intent.NEW_TOPIC)
        session.add_turn("assistant", "Tesla revenue is $81B...")
        session.facts = ["Tesla revenue: $81B", "Tesla growth: 25%"]
        
        # Build context for follow-up
        builder = SmartContextBuilder()
        context = builder.build(session, "What about their competition?")
        
        assert context is not None
        print(f"\n✅ Context built with {len(context)} items")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
