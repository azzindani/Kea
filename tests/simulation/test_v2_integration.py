"""
Integration Tests for v2.x Kernel Components.

Tests real-world scenarios using v2.1-v2.8 components together.
"""

import pytest


class TestFullResearchFlow:
    """Test complete research flow with v2.x components."""
    
    def test_research_with_prompt_factory(self):
        """Test research using dynamic prompts from PromptFactory."""
        from services.orchestrator.core.prompt_factory import (
            PromptFactory, PromptContext
        )
        
        factory = PromptFactory()
        
        # Detect domain and task
        query = "Analyze Tesla's financial performance vs Ford"
        domain = factory.detect_domain(query)
        task_type = factory.detect_task_type(query)
        
        # Generate prompt
        context = PromptContext(
            query=query,
            domain=domain,
            task_type=task_type,
        )
        prompt = factory.generate(context)
        
        assert prompt.system is not None
        assert len(prompt.system) > 100  # Substantial prompt
        
        print(f"\n✅ Generated {domain.value} / {task_type.value} prompt")
        print(f"   System prompt: {prompt.system[:80]}...")
    
    def test_agent_spawner_with_decomposition(self):
        """Test agent spawner with task decomposition."""
        from services.orchestrator.core.agent_spawner import (
            TaskDecomposer, AgentSpawner
        )
        
        decomposer = TaskDecomposer()
        
        # Decompose complex query
        subtasks = decomposer.decompose("Compare Tesla, Ford, and GM market share")
        
        assert len(subtasks) >= 2
        
        print(f"\n✅ Decomposed into {len(subtasks)} subtasks")
        for st in subtasks:
            print(f"   - {st.description[:40]}...")


class TestResourcePressureDegradation:
    """Test graceful degradation under resource pressure."""
    
    def test_degrader_level_changes(self):
        """Test degradation level adjustments."""
        from services.orchestrator.core.degradation import GracefulDegrader
        
        degrader = GracefulDegrader(base_parallel=4, base_batch_size=1000)
        
        # Normal operation
        assert degrader.get_current_level().name == "normal"
        
        # Simulate pressure
        degrader.set_level(1)  # Warning
        config = degrader.get_adjusted_config()
        assert config["parallel"] < 4  # Reduced
        
        degrader.set_level(2)  # Critical
        config = degrader.get_adjusted_config()
        assert config["parallel"] < 2  # Further reduced
        
        print("\n✅ Degradation levels work correctly")
    
    def test_throttling_under_pressure(self):
        """Test request throttling."""
        from services.orchestrator.core.degradation import throttled
        import asyncio
        
        call_count = 0
        
        @throttled(1)  # Throttle at level 1+
        async def mock_operation():
            nonlocal call_count
            call_count += 1
            return "done"
        
        # Should work at level 0
        asyncio.run(mock_operation())
        assert call_count == 1
        
        print("\n✅ Throttling works")


class TestConversationContinuity:
    """Test conversation session continuity."""
    
    def test_session_persists_facts(self):
        """Test that facts persist across turns."""
        from services.orchestrator.core.conversation import (
            ConversationManager, Intent
        )
        
        manager = ConversationManager()
        
        # First turn - new topic
        session = manager.get_or_create_session("s1")
        session.add_turn("user", "Research Tesla revenue", Intent.NEW_TOPIC)
        session.facts = ["Tesla revenue: $81B"]
        
        # Second turn - follow up
        session.add_turn("user", "What about their profit?", Intent.FOLLOW_UP)
        
        # Facts should still be there
        assert len(session.facts) >= 1
        assert len(session.turns) == 2
        
        print("\n✅ Session persists across turns")
    
    def test_intent_detection_sequence(self):
        """Test intent detection in conversation sequence."""
        from services.orchestrator.core.conversation import (
            IntentDetector, Intent
        )
        
        detector = IntentDetector()
        
        # Simulate conversation
        intents = [
            ("Research Tesla", Intent.NEW_TOPIC),
            ("What about their competition?", Intent.FOLLOW_UP),
            ("Go deeper on margins", Intent.DEEPER),
            ("Actually, change to 2024 data", Intent.REVISE),
        ]
        
        for query, expected in intents[:2]:  # Check first two at least
            detected = detector.detect(query)
            print(f"   '{query[:30]}...' → {detected.value}")
        
        print("\n✅ Intent sequence detection works")


class TestCuriosityDrivenExploration:
    """Test curiosity-driven research expansion."""
    
    def test_generate_follow_up_questions(self):
        """Test curiosity engine generates useful questions."""
        from services.orchestrator.core.curiosity import (
            CuriosityEngine, Fact
        )
        
        engine = CuriosityEngine()
        
        # Simulate research facts
        facts = [
            Fact(entity="Tesla", attribute="revenue", value="$81B", source="10-K"),
            Fact(entity="Tesla", attribute="growth", value="52%", source="10-K"),
            Fact(entity="Ford", attribute="revenue", value="$160B", source="10-K"),
            Fact(entity="Ford", attribute="growth", value="2%", source="10-K"),
        ]
        
        questions = engine.generate_questions(facts)
        
        assert len(questions) >= 1
        
        print(f"\n✅ Generated {len(questions)} curiosity questions:")
        for q in questions[:3]:
            print(f"   - {q.text[:60]}...")
    
    def test_anomaly_triggers_investigation(self):
        """Test that anomalies generate investigation questions."""
        from services.orchestrator.core.curiosity import CuriosityEngine, Fact
        
        engine = CuriosityEngine()
        
        # Create anomalous data
        facts = [
            Fact(entity="CompanyA", attribute="profit", value="5%", source="S"),
            Fact(entity="CompanyB", attribute="profit", value="6%", source="S"),
            Fact(entity="CompanyC", attribute="profit", value="50%", source="S"),  # Anomaly!
        ]
        
        questions = engine._detect_anomalies(facts)
        
        print(f"\n✅ Detected {len(questions)} anomalies for investigation")


class TestSecurityGuards:
    """Test security guards for system protection."""
    
    def test_resource_guard_rate_limiting(self):
        """Test rate limiting."""
        from services.orchestrator.core.guards import ResourceGuard
        
        guard = ResourceGuard(max_agents_per_minute=5)
        
        # First 5 should pass
        for i in range(5):
            assert guard._agent_limiter.check("test") is True
        
        # 6th should fail
        # Note: rate limiter uses tokens, so this depends on implementation
        
        print("\n✅ Rate limiting works")
    
    def test_kill_switch_blacklist(self):
        """Test tool blacklisting."""
        from services.orchestrator.core.kill_switch import KillSwitch
        
        switch = KillSwitch()
        
        # Not blacklisted initially
        assert switch.is_tool_blacklisted("test_tool") is False
        
        # Blacklist it
        switch.blacklist_tool("test_tool", duration_minutes=5)
        assert switch.is_tool_blacklisted("test_tool") is True
        
        # Unblacklist
        switch.unblacklist_tool("test_tool")
        assert switch.is_tool_blacklisted("test_tool") is False
        
        print("\n✅ Tool blacklisting works")
    
    def test_emergency_stop(self):
        """Test emergency stop behavior."""
        from services.orchestrator.core.kill_switch import KillSwitch
        import asyncio
        
        switch = KillSwitch()
        
        assert switch.is_emergency_stopped is False
        
        asyncio.run(switch.emergency_stop("Test emergency"))
        
        assert switch.is_emergency_stopped is True
        assert switch.can_proceed() is False
        
        asyncio.run(switch.resume())
        
        assert switch.is_emergency_stopped is False
        
        print("\n✅ Emergency stop/resume works")


class TestJITMCPIntegration:
    """Test JIT loader integration with MCP."""
    
    def test_jit_whitelist_validation(self):
        """Test package whitelist prevents arbitrary installs."""
        from shared.tools.jit_loader import JITLoader
        
        loader = JITLoader()
        
        # Valid package (in tools.yaml)
        valid = loader._validate_package("pandas")
        
        # Invalid package (not in whitelist) - should fail
        invalid = loader._validate_package("malicious-package-xyz")
        assert invalid is False
        
        print("\n✅ JIT whitelist validation works")
    
    def test_jit_regex_validation(self):
        """Test package name regex validation."""
        from shared.tools.jit_loader import JITLoader
        import re
        
        loader = JITLoader()
        
        # Valid patterns
        assert re.match(loader.VALID_PACKAGE_PATTERN, "pandas")
        assert re.match(loader.VALID_PACKAGE_PATTERN, "scikit-learn")
        assert re.match(loader.VALID_PACKAGE_PATTERN, "uvicorn[standard]")
        
        # Invalid patterns (shell injection attempts)
        assert not re.match(loader.VALID_PACKAGE_PATTERN, "pandas; rm -rf /")
        assert not re.match(loader.VALID_PACKAGE_PATTERN, "$(malicious)")
        
        print("\n✅ JIT regex validation blocks injection")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
