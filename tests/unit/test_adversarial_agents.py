"""
Tests for Adversarial Collaboration Agents.

Tests generator (optimist), critic (pessimist), and judge (synthesizer) agents.
"""

import pytest


class TestGeneratorAgent:
    """Tests for Generator (The Optimist)."""
    
    def test_import_generator(self):
        """Test generator module imports."""
        from services.orchestrator.agents.generator import (
            Generator,
            generate,
        )
        
        assert Generator is not None or generate is not None
        print("\n✅ Generator imports work")
    
    def test_create_generator(self):
        """Test generator creation."""
        from services.orchestrator.agents.generator import Generator
        
        gen = Generator()
        
        assert gen is not None
        print("\n✅ Generator created")
    
    def test_generate_optimistic_view(self):
        """Test generating optimistic perspective."""
        from services.orchestrator.agents.generator import Generator
        
        gen = Generator()
        
        topic = "Tesla's future growth"
        facts = ["Revenue grew 25%", "Market leader in EVs"]
        
        perspective = gen.generate(topic, facts)
        
        assert perspective is not None
        assert hasattr(perspective, "content") or isinstance(perspective, dict)
        
        print("\n✅ Optimistic perspective generated")
    
    def test_confidence_score(self):
        """Test confidence scoring."""
        from services.orchestrator.agents.generator import Generator
        
        gen = Generator()
        
        claim = "Tesla will dominate EV market"
        evidence = ["Market share: 60%", "Brand strength", "Supercharger network"]
        
        score = gen.score_confidence(claim, evidence)
        
        assert 0 <= score <= 1
        
        print(f"\n✅ Confidence score: {score:.2f}")


class TestCriticAgent:
    """Tests for Critic (The Pessimist)."""
    
    def test_import_critic(self):
        """Test critic module imports."""
        from services.orchestrator.agents.critic import (
            Critic,
            critique,
        )
        
        assert Critic is not None or critique is not None
        print("\n✅ Critic imports work")
    
    def test_create_critic(self):
        """Test critic creation."""
        from services.orchestrator.agents.critic import Critic
        
        critic = Critic()
        
        assert critic is not None
        print("\n✅ Critic created")
    
    def test_generate_critique(self):
        """Test generating critical perspective."""
        from services.orchestrator.agents.critic import Critic
        
        critic = Critic()
        
        claim = "Tesla will grow 50% next year"
        evidence = ["Past growth 25%", "Competition increasing"]
        
        critique = critic.critique(claim, evidence)
        
        assert critique is not None
        
        print("\n✅ Critique generated")
    
    def test_find_weaknesses(self):
        """Test finding weaknesses in argument."""
        from services.orchestrator.agents.critic import Critic
        
        critic = Critic()
        
        argument = {
            "claim": "Stock will rise",
            "evidence": ["One analyst said so"],
        }
        
        weaknesses = critic.find_weaknesses(argument)
        
        assert isinstance(weaknesses, list)
        
        print(f"\n✅ Found {len(weaknesses)} weaknesses")
    
    def test_suggest_alternatives(self):
        """Test suggesting alternative interpretations."""
        from services.orchestrator.agents.critic import Critic
        
        critic = Critic()
        
        interpretation = "Revenue drop indicates company failure"
        
        alternatives = critic.suggest_alternatives(interpretation)
        
        assert isinstance(alternatives, list)
        
        print(f"\n✅ Suggested {len(alternatives)} alternatives")


class TestJudgeAgent:
    """Tests for Judge (The Synthesizer)."""
    
    def test_import_judge(self):
        """Test judge module imports."""
        from services.orchestrator.agents.judge import (
            Judge,
            judge,
        )
        
        assert Judge is not None or judge is not None
        print("\n✅ Judge imports work")
    
    def test_create_judge(self):
        """Test judge creation."""
        from services.orchestrator.agents.judge import Judge
        
        j = Judge()
        
        assert j is not None
        print("\n✅ Judge created")
    
    def test_evaluate_perspectives(self):
        """Test evaluating opposing perspectives."""
        from services.orchestrator.agents.judge import Judge
        
        j = Judge()
        
        optimist = {"view": "Strong growth ahead", "confidence": 0.8}
        pessimist = {"view": "Headwinds ahead", "confidence": 0.6}
        
        evaluation = j.evaluate(optimist, pessimist)
        
        assert evaluation is not None
        
        print("\n✅ Perspectives evaluated")
    
    def test_synthesize_verdict(self):
        """Test synthesizing final verdict."""
        from services.orchestrator.agents.judge import Judge
        
        j = Judge()
        
        perspectives = [
            {"agent": "generator", "claim": "Bullish", "score": 0.8},
            {"agent": "critic", "claim": "Bearish", "score": 0.6},
        ]
        
        verdict = j.synthesize(perspectives)
        
        assert verdict is not None
        assert hasattr(verdict, "conclusion") or "conclusion" in str(verdict)
        
        print("\n✅ Verdict synthesized")
    
    def test_balance_views(self):
        """Test balancing conflicting views."""
        from services.orchestrator.agents.judge import Judge
        
        j = Judge()
        
        views = [
            {"position": "pro", "strength": 0.9},
            {"position": "con", "strength": 0.7},
        ]
        
        balanced = j.balance(views)
        
        assert balanced is not None
        
        print("\n✅ Views balanced")
    
    def test_identify_consensus(self):
        """Test identifying areas of consensus."""
        from services.orchestrator.agents.judge import Judge
        
        j = Judge()
        
        claims = [
            {"agent": "A", "claims": ["Tesla is an EV company", "Revenue is high"]},
            {"agent": "B", "claims": ["Tesla is an EV company", "Growth may slow"]},
        ]
        
        consensus = j.find_consensus(claims)
        
        assert isinstance(consensus, list)
        
        print(f"\n✅ Found {len(consensus)} consensus points")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
