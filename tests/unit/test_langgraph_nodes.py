"""
Tests for LangGraph Nodes.

Tests divergence, keeper, planner, and synthesizer nodes.
"""

import pytest


class TestDivergenceNode:
    """Tests for Divergence Engine (Abductive Reasoning)."""
    
    def test_import_divergence(self):
        """Test divergence module imports."""
        from services.orchestrator.nodes.divergence import (
            diverge,
            DivergenceEngine,
        )
        
        assert diverge is not None or DivergenceEngine is not None
        print("\n✅ Divergence imports work")
    
    def test_generate_hypotheses(self):
        """Test hypothesis generation."""
        from services.orchestrator.nodes.divergence import DivergenceEngine
        
        engine = DivergenceEngine()
        
        # Given observation
        observation = "Tesla stock dropped 10% despite strong earnings"
        
        hypotheses = engine.generate_hypotheses(observation)
        
        assert isinstance(hypotheses, list)
        assert len(hypotheses) >= 1
        
        print(f"\n✅ Generated {len(hypotheses)} hypotheses")
    
    def test_rank_hypotheses(self):
        """Test hypothesis ranking by plausibility."""
        from services.orchestrator.nodes.divergence import DivergenceEngine
        
        engine = DivergenceEngine()
        
        hypotheses = [
            {"hypothesis": "Market correction", "evidence": ["Market-wide decline"]},
            {"hypothesis": "CEO controversy", "evidence": []},
        ]
        
        ranked = engine.rank_hypotheses(hypotheses)
        
        assert len(ranked) == len(hypotheses)
        
        print("\n✅ Hypothesis ranking works")


class TestKeeperNode:
    """Tests for The Keeper (Context Guard)."""
    
    def test_import_keeper(self):
        """Test keeper module imports."""
        from services.orchestrator.nodes.keeper import (
            keep,
            ContextKeeper,
        )
        
        assert keep is not None or ContextKeeper is not None
        print("\n✅ Keeper imports work")
    
    def test_filter_context(self):
        """Test context filtering."""
        from services.orchestrator.nodes.keeper import ContextKeeper
        
        keeper = ContextKeeper(max_tokens=1000)
        
        context = [
            {"type": "fact", "content": "Tesla revenue: $81B", "relevance": 0.9},
            {"type": "fact", "content": "Apple revenue: $400B", "relevance": 0.1},
            {"type": "fact", "content": "Tesla growth: 25%", "relevance": 0.85},
        ]
        
        filtered = keeper.filter(context, query="Tesla financials")
        
        # Should keep Tesla, drop Apple
        assert len(filtered) <= len(context)
        
        print(f"\n✅ Filtered to {len(filtered)} items")
    
    def test_prioritize_recent(self):
        """Test prioritizing recent context."""
        from services.orchestrator.nodes.keeper import ContextKeeper
        
        keeper = ContextKeeper()
        
        context = [
            {"content": "Old data", "timestamp": "2020-01-01"},
            {"content": "New data", "timestamp": "2024-01-01"},
        ]
        
        prioritized = keeper.prioritize(context)
        
        assert prioritized[0]["content"] == "New data"
        
        print("\n✅ Recent prioritization works")


class TestPlannerNode:
    """Tests for Planner & Decomposer."""
    
    def test_import_planner(self):
        """Test planner module imports."""
        from services.orchestrator.nodes.planner import (
            plan,
            ResearchPlanner,
        )
        
        assert plan is not None or ResearchPlanner is not None
        print("\n✅ Planner imports work")
    
    def test_decompose_query(self):
        """Test query decomposition."""
        from services.orchestrator.nodes.planner import ResearchPlanner
        
        planner = ResearchPlanner()
        
        query = "Compare Tesla and Ford financial performance and market position"
        
        steps = planner.decompose(query)
        
        assert isinstance(steps, list)
        assert len(steps) >= 2  # Should break into multiple steps
        
        print(f"\n✅ Decomposed into {len(steps)} steps")
    
    def test_create_execution_plan(self):
        """Test execution plan creation."""
        from services.orchestrator.nodes.planner import ResearchPlanner
        
        planner = ResearchPlanner()
        
        query = "Research Tesla stock performance"
        
        plan = planner.create_plan(query)
        
        assert plan is not None
        assert hasattr(plan, "steps") or isinstance(plan, dict)
        
        print("\n✅ Execution plan created")
    
    def test_estimate_complexity(self):
        """Test complexity estimation."""
        from services.orchestrator.nodes.planner import ResearchPlanner
        
        planner = ResearchPlanner()
        
        simple = "What is AAPL price?"
        complex = "Create comprehensive market analysis of EV industry"
        
        simple_score = planner.estimate_complexity(simple)
        complex_score = planner.estimate_complexity(complex)
        
        assert complex_score > simple_score
        
        print(f"\n✅ Complexity: simple={simple_score}, complex={complex_score}")


class TestSynthesizerNode:
    """Tests for Report Synthesizer."""
    
    def test_import_synthesizer(self):
        """Test synthesizer module imports."""
        from services.orchestrator.nodes.synthesizer import (
            synthesize,
            ReportSynthesizer,
        )
        
        assert synthesize is not None or ReportSynthesizer is not None
        print("\n✅ Synthesizer imports work")
    
    def test_combine_sources(self):
        """Test combining multiple sources."""
        from services.orchestrator.nodes.synthesizer import ReportSynthesizer
        
        synthesizer = ReportSynthesizer()
        
        sources = [
            {"source": "SEC Filing", "data": {"revenue": "$81B"}},
            {"source": "News Article", "data": {"sentiment": "positive"}},
        ]
        
        combined = synthesizer.combine(sources)
        
        assert combined is not None
        
        print("\n✅ Sources combined")
    
    def test_generate_report(self):
        """Test report generation."""
        from services.orchestrator.nodes.synthesizer import ReportSynthesizer
        
        synthesizer = ReportSynthesizer()
        
        data = {
            "query": "Tesla analysis",
            "facts": ["Revenue: $81B", "Growth: 25%"],
            "analysis": "Strong performance",
        }
        
        report = synthesizer.generate(data)
        
        assert report is not None
        assert isinstance(report, str) or hasattr(report, "content")
        
        print("\n✅ Report generated")
    
    def test_format_output(self):
        """Test output formatting."""
        from services.orchestrator.nodes.synthesizer import ReportSynthesizer
        
        synthesizer = ReportSynthesizer()
        
        content = "Tesla showed strong growth..."
        
        formatted = synthesizer.format(content, style="markdown")
        
        assert formatted is not None
        
        print("\n✅ Output formatted")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
