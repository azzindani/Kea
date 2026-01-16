"""
Tests for adversarial agents (Generator, Critic, Judge).
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestGeneratorAgent:
    """Tests for GeneratorAgent."""
    
    def test_import_generator(self):
        """Test that generator can be imported."""
        from services.orchestrator.agents.generator import GeneratorAgent
        assert GeneratorAgent is not None
    
    def test_create_generator(self):
        """Test creating generator instance."""
        from services.orchestrator.agents.generator import GeneratorAgent
        generator = GeneratorAgent()
        assert generator.name == "Generator"
        assert generator.role == "The Optimist"
    
    @pytest.mark.asyncio
    async def test_fallback_generate(self):
        """Test fallback generation without LLM."""
        from services.orchestrator.agents.generator import GeneratorAgent
        generator = GeneratorAgent()
        
        result = generator._fallback_generate(
            query="Test query",
            facts=["Fact 1", "Fact 2"],
            sources=["Source 1"]
        )
        
        assert "Test query" in result
        assert "2 collected facts" in result
    
    @pytest.mark.asyncio
    async def test_generate_without_api_key(self):
        """Test generate uses fallback when no API key."""
        from services.orchestrator.agents.generator import GeneratorAgent
        generator = GeneratorAgent()
        
        with patch.dict('os.environ', {}, clear=True):
            result = await generator.generate(
                query="What is AI?",
                facts=["AI is artificial intelligence"],
                sources=["wiki"]
            )
        
        assert result is not None
        assert isinstance(result, str)


class TestCriticAgent:
    """Tests for CriticAgent."""
    
    def test_import_critic(self):
        """Test that critic can be imported."""
        from services.orchestrator.agents.critic import CriticAgent
        assert CriticAgent is not None
    
    def test_create_critic(self):
        """Test creating critic instance."""
        from services.orchestrator.agents.critic import CriticAgent
        critic = CriticAgent()
        assert critic.name == "Critic"
        assert critic.role == "The Pessimist"
    
    def test_fallback_critique(self):
        """Test fallback critique without LLM."""
        from services.orchestrator.agents.critic import CriticAgent
        critic = CriticAgent()
        
        result = critic._fallback_critique("This is an answer with sources.")
        
        assert "Critique" in result
        assert "Present" in result  # Source mentioned
    
    @pytest.mark.asyncio
    async def test_critique_without_api_key(self):
        """Test critique uses fallback when no API key."""
        from services.orchestrator.agents.critic import CriticAgent
        critic = CriticAgent()
        
        with patch.dict('os.environ', {}, clear=True):
            result = await critic.critique(
                answer="AI is very useful",
                facts=["AI fact"],
                sources=["source"]
            )
        
        assert result is not None
        assert "Critique" in result


class TestJudgeAgent:
    """Tests for JudgeAgent."""
    
    def test_import_judge(self):
        """Test that judge can be imported."""
        from services.orchestrator.agents.judge import JudgeAgent
        assert JudgeAgent is not None
    
    def test_create_judge(self):
        """Test creating judge instance."""
        from services.orchestrator.agents.judge import JudgeAgent
        judge = JudgeAgent()
        assert judge.name == "Judge"
        assert judge.role == "The Synthesizer"
    
    def test_fallback_judge(self):
        """Test fallback judgment without LLM."""
        from services.orchestrator.agents.judge import JudgeAgent
        judge = JudgeAgent()
        
        result = judge._fallback_judge(
            generator_output="Generated answer",
            critic_feedback="Critique feedback"
        )
        
        assert result["verdict"] == "Accept"
        assert result["confidence"] == 0.5
        assert "final_answer" in result
    
    @pytest.mark.asyncio
    async def test_judge_without_api_key(self):
        """Test judge uses fallback when no API key."""
        from services.orchestrator.agents.judge import JudgeAgent
        judge = JudgeAgent()
        
        with patch.dict('os.environ', {}, clear=True):
            result = await judge.judge(
                query="Test query",
                generator_output="Generator's answer",
                critic_feedback="Critic's feedback"
            )
        
        assert result is not None
        assert "verdict" in result
        assert "confidence" in result
