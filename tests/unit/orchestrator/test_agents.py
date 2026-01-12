"""
Unit Tests: Orchestrator Agents.

Tests for services/orchestrator/agents/*.py
"""

import pytest


class TestGeneratorAgent:
    """Tests for generator agent."""
    
    def test_generator_init(self):
        """Generator initializes correctly."""
        from services.orchestrator.agents.generator import GeneratorAgent
        
        agent = GeneratorAgent()
        
        assert agent.name == "Generator"
        assert agent.role == "The Optimist"
    
    @pytest.mark.asyncio
    async def test_generator_fallback(self):
        """Generator fallback works without LLM."""
        from services.orchestrator.agents.generator import GeneratorAgent
        import os
        
        # Ensure no API key
        old_key = os.environ.pop("OPENROUTER_API_KEY", None)
        
        try:
            agent = GeneratorAgent()
            result = await agent.generate(
                query="Test",
                facts=[{"text": "Fact 1"}],
                sources=[]
            )
            
            assert "Test" in result or "fact" in result.lower()
        finally:
            if old_key:
                os.environ["OPENROUTER_API_KEY"] = old_key


class TestCriticAgent:
    """Tests for critic agent."""
    
    def test_critic_init(self):
        """Critic initializes correctly."""
        from services.orchestrator.agents.critic import CriticAgent
        
        agent = CriticAgent()
        
        assert agent.name == "Critic"
        assert agent.role == "The Pessimist"
    
    @pytest.mark.asyncio
    async def test_critic_fallback(self):
        """Critic fallback works without LLM."""
        from services.orchestrator.agents.critic import CriticAgent
        import os
        
        old_key = os.environ.pop("OPENROUTER_API_KEY", None)
        
        try:
            agent = CriticAgent()
            result = await agent.critique(
                answer="Test answer",
                facts=[],
                sources=[]
            )
            
            assert "Critique" in result
        finally:
            if old_key:
                os.environ["OPENROUTER_API_KEY"] = old_key


class TestJudgeAgent:
    """Tests for judge agent."""
    
    def test_judge_init(self):
        """Judge initializes correctly."""
        from services.orchestrator.agents.judge import JudgeAgent
        
        agent = JudgeAgent()
        
        assert agent.name == "Judge"
        assert agent.role == "The Synthesizer"
    
    @pytest.mark.asyncio
    async def test_judge_fallback(self):
        """Judge fallback works without LLM."""
        from services.orchestrator.agents.judge import JudgeAgent
        import os
        
        old_key = os.environ.pop("OPENROUTER_API_KEY", None)
        
        try:
            agent = JudgeAgent()
            result = await agent.judge(
                query="Test",
                generator_output="Answer",
                critic_feedback="Critique"
            )
            
            assert "verdict" in result
            assert "confidence" in result
        finally:
            if old_key:
                os.environ["OPENROUTER_API_KEY"] = old_key


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
