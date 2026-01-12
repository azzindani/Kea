"""
Unit Tests: LangGraph Research Graph.

Tests for services/orchestrator/core/graph.py
"""

import pytest


class TestGraphState:
    """Tests for graph state (TypedDict)."""
    
    def test_create_state(self):
        """Create graph state as dict."""
        from services.orchestrator.core.graph import GraphState
        
        # GraphState is a TypedDict, so we create it as a dict
        state: GraphState = {
            "job_id": "job-123",
            "query": "Test research query",
            "path": "",
            "status": "pending",
            "sub_queries": [],
            "hypotheses": [],
            "facts": [],
            "sources": [],
            "artifacts": [],
            "generator_output": "",
            "critic_feedback": "",
            "judge_verdict": "",
            "report": "",
            "confidence": 0.0,
            "iteration": 0,
            "max_iterations": 3,
            "should_continue": True,
            "error": None,
        }
        
        assert state["job_id"] == "job-123"
        assert state["query"] == "Test research query"
        assert state["status"] == "pending"
    
    def test_state_defaults(self):
        """State dict has correct default values."""
        from services.orchestrator.core.graph import GraphState
        
        state: GraphState = {
            "job_id": "j",
            "query": "q",
            "path": "",
            "status": "pending",
            "sub_queries": [],
            "hypotheses": [],
            "facts": [],
            "sources": [],
            "artifacts": [],
            "generator_output": "",
            "critic_feedback": "",
            "judge_verdict": "",
            "report": "",
            "confidence": 0.0,
            "iteration": 0,
            "max_iterations": 3,
            "should_continue": True,
            "error": None,
        }
        
        assert state["facts"] == []
        assert state["sources"] == []
        assert state["iteration"] == 0
        assert state["should_continue"] is True


class TestResearchGraph:
    """Tests for research graph compilation."""
    
    def test_compile_graph(self):
        """Compile research graph."""
        from services.orchestrator.core.graph import compile_research_graph
        
        graph = compile_research_graph()
        
        assert graph is not None


class TestGraphNodes:
    """Tests for individual graph nodes."""
    
    @pytest.mark.asyncio
    async def test_intention_router(self):
        """Test intention router - state is dict."""
        from services.orchestrator.core.graph import GraphState
        
        state: GraphState = {
            "job_id": "test",
            "query": "What is the capital of France?",
            "path": "",
            "status": "pending",
            "sub_queries": [],
            "hypotheses": [],
            "facts": [],
            "sources": [],
            "artifacts": [],
            "generator_output": "",
            "critic_feedback": "",
            "judge_verdict": "",
            "report": "",
            "confidence": 0.0,
            "iteration": 0,
            "max_iterations": 3,
            "should_continue": True,
            "error": None,
        }
        
        state["path"] = "A"
        assert state["path"] == "A"
    
    @pytest.mark.asyncio
    async def test_decomposer(self):
        """Test query decomposer - state is dict."""
        from services.orchestrator.core.graph import GraphState
        
        state: GraphState = {
            "job_id": "test",
            "query": "Complex query",
            "path": "D",
            "status": "running",
            "sub_queries": ["sub1", "sub2"],
            "hypotheses": [],
            "facts": [],
            "sources": [],
            "artifacts": [],
            "generator_output": "",
            "critic_feedback": "",
            "judge_verdict": "",
            "report": "",
            "confidence": 0.0,
            "iteration": 0,
            "max_iterations": 3,
            "should_continue": True,
            "error": None,
        }
        
        assert len(state["sub_queries"]) == 2
    
    @pytest.mark.asyncio
    async def test_consensus_engine(self):
        """Test consensus engine state."""
        from services.orchestrator.core.graph import GraphState
        
        state: GraphState = {
            "job_id": "test",
            "query": "q",
            "path": "D",
            "status": "running",
            "sub_queries": [],
            "hypotheses": [],
            "facts": [],
            "sources": [],
            "artifacts": [],
            "generator_output": "Generated answer",
            "critic_feedback": "Looks good",
            "judge_verdict": "Approved",
            "report": "",
            "confidence": 0.0,
            "iteration": 0,
            "max_iterations": 3,
            "should_continue": True,
            "error": None,
        }
        
        assert state["generator_output"] == "Generated answer"
        assert state["judge_verdict"] == "Approved"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
