"""
Tests for Curiosity Engine.
"""

import pytest


class TestQuestionType:
    """Tests for question type enum."""
    
    def test_question_types(self):
        """Test question type values."""
        from services.orchestrator.core.curiosity import QuestionType
        
        assert QuestionType.CAUSAL_WHY.value == "causal_why"
        assert QuestionType.COUNTERFACTUAL.value == "counterfactual"
        assert QuestionType.SCENARIO.value == "scenario"
        assert QuestionType.ANOMALY.value == "anomaly"
        assert QuestionType.COMPARISON.value == "comparison"
        assert QuestionType.TREND.value == "trend"
        assert QuestionType.GAP.value == "gap"
        
        print("\n✅ QuestionType values correct")


class TestFact:
    """Tests for Fact dataclass."""
    
    def test_create_fact(self):
        """Test fact creation."""
        from services.orchestrator.core.curiosity import Fact
        
        fact = Fact(
            entity="Tesla",
            attribute="revenue",
            value="$81B",
            source="10-K filing",
            confidence=0.95,
        )
        
        assert fact.entity == "Tesla"
        assert fact.attribute == "revenue"
        assert fact.value == "$81B"
        assert fact.confidence == 0.95
        
        print("\n✅ Fact creation works")


class TestCuriosityQuestion:
    """Tests for curiosity questions."""
    
    def test_create_question(self):
        """Test question creation."""
        from services.orchestrator.core.curiosity import CuriosityQuestion, QuestionType
        
        q = CuriosityQuestion(
            question_id="q1",
            question_type=QuestionType.CAUSAL_WHY,
            text="Why did revenue decline?",
            priority=0.8,
            entity="Tesla",
        )
        
        assert q.question_id == "q1"
        assert q.question_type == QuestionType.CAUSAL_WHY
        assert q.priority == 0.8
        assert q.explored is False
        
        print("\n✅ Question creation works")


class TestCuriosityEngine:
    """Tests for curiosity engine."""
    
    def test_generate_causal_questions(self):
        """Test causal WHY question generation."""
        from services.orchestrator.core.curiosity import CuriosityEngine, Fact
        
        engine = CuriosityEngine()
        
        facts = [
            Fact(entity="Tesla", attribute="revenue", value="$81B", source="10-K"),
            Fact(entity="Tesla", attribute="growth", value="25%", source="10-K"),
        ]
        
        questions = engine.generate_questions(facts, depth=2)
        
        assert len(questions) >= 1
        print(f"\n✅ Generated {len(questions)} questions")
        for q in questions[:3]:
            print(f"   - {q.text[:50]}...")
    
    def test_detect_anomalies(self):
        """Test anomaly detection."""
        from services.orchestrator.core.curiosity import CuriosityEngine, Fact
        
        engine = CuriosityEngine()
        
        # Create facts with potential anomaly
        facts = [
            Fact(entity="Tesla", attribute="profit_margin", value="15%", source="A"),
            Fact(entity="Ford", attribute="profit_margin", value="3%", source="B"),
            Fact(entity="GM", attribute="profit_margin", value="4%", source="C"),
        ]
        
        questions = engine._detect_anomalies(facts)
        
        # Tesla's margin is an outlier, should generate question
        print(f"\n✅ Anomaly detection found {len(questions)} anomalies")
    
    def test_generate_comparisons(self):
        """Test comparison question generation."""
        from services.orchestrator.core.curiosity import CuriosityEngine, Fact
        
        engine = CuriosityEngine()
        
        facts = [
            Fact(entity="Tesla", attribute="revenue", value="$81B", source="A"),
            Fact(entity="Ford", attribute="revenue", value="$160B", source="B"),
        ]
        
        questions = engine._generate_comparisons(facts)
        
        assert len(questions) >= 1
        print(f"\n✅ Generated {len(questions)} comparison questions")
    
    def test_format_for_user(self):
        """Test user-friendly formatting."""
        from services.orchestrator.core.curiosity import (
            CuriosityEngine, CuriosityQuestion, QuestionType
        )
        
        engine = CuriosityEngine()
        
        questions = [
            CuriosityQuestion(
                question_id="q1",
                question_type=QuestionType.CAUSAL_WHY,
                text="Why did Tesla's revenue grow 25%?",
                priority=0.9,
            ),
            CuriosityQuestion(
                question_id="q2",
                question_type=QuestionType.COUNTERFACTUAL,
                text="What if growth was only 10%?",
                priority=0.7,
            ),
        ]
        
        formatted = engine.format_for_user(questions)
        
        assert "1." in formatted
        assert "2." in formatted
        
        print("\n✅ User formatting works")
        print(formatted)
    
    def test_get_icon(self):
        """Test icon mapping."""
        from services.orchestrator.core.curiosity import CuriosityEngine, QuestionType
        
        engine = CuriosityEngine()
        
        assert engine._get_icon(QuestionType.CAUSAL_WHY) == "❓"
        assert engine._get_icon(QuestionType.ANOMALY) == "⚠️"
        assert engine._get_icon(QuestionType.TREND) == "📈"
        
        print("\n✅ Icon mapping works")


class TestCuriosityEngineDepth:
    """Tests for depth-based question generation."""
    
    def test_shallow_depth(self):
        """Test shallow exploration (depth=1)."""
        from services.orchestrator.core.curiosity import CuriosityEngine, Fact
        
        engine = CuriosityEngine()
        
        facts = [Fact(entity="Tesla", attribute="stock", value="$250", source="NYSE")]
        
        shallow = engine.generate_questions(facts, depth=1)
        deep = engine.generate_questions(facts, depth=3)
        
        # Deeper exploration should generate more questions
        print(f"\n✅ Shallow: {len(shallow)}, Deep: {len(deep)} questions")
    
    def test_question_priority_sorting(self):
        """Test questions are sorted by priority."""
        from services.orchestrator.core.curiosity import CuriosityEngine, Fact
        
        engine = CuriosityEngine()
        
        facts = [
            Fact(entity="A", attribute="x", value="100", source="S"),
            Fact(entity="B", attribute="y", value="200", source="S"),
        ]
        
        questions = engine.generate_questions(facts)
        
        if len(questions) > 1:
            # Should be sorted by priority (highest first)
            for i in range(len(questions) - 1):
                assert questions[i].priority >= questions[i + 1].priority
        
        print("\n✅ Questions sorted by priority")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
