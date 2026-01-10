"""
Orchestrator Tests.

Tests for the orchestrator service components.
"""

import pytest
import asyncio


# ============================================================================
# Graph Tests
# ============================================================================

class TestResearchGraph:
    """Tests for the LangGraph research state machine."""
    
    @pytest.mark.asyncio
    async def test_router_node(self):
        """Test router node classification."""
        from services.orchestrator.core.graph import router_node, GraphState
        
        state: GraphState = {
            "job_id": "test-job",
            "query": "What are the latest nickel production figures?",
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
        
        result = await router_node(state)
        
        assert result["path"] == "D"  # Deep research
        assert result["status"] == "running"
    
    @pytest.mark.asyncio
    async def test_planner_node(self):
        """Test planner node decomposition."""
        from services.orchestrator.core.graph import planner_node, GraphState
        
        state: GraphState = {
            "job_id": "test-job",
            "query": "Indonesia nickel production",
            "path": "D",
            "status": "running",
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
        
        result = await planner_node(state)
        
        assert len(result["sub_queries"]) > 0
        assert len(result["hypotheses"]) > 0
        assert result["iteration"] == 1
    
    @pytest.mark.asyncio
    async def test_keeper_node_continue(self):
        """Test keeper node decides to continue."""
        from services.orchestrator.core.graph import keeper_node, GraphState
        
        state: GraphState = {
            "job_id": "test-job",
            "query": "test",
            "path": "D",
            "status": "running",
            "sub_queries": [],
            "hypotheses": [],
            "facts": [{"entity": "test", "value": "1"}],  # Only 1 fact
            "sources": [],
            "artifacts": [],
            "generator_output": "",
            "critic_feedback": "",
            "judge_verdict": "",
            "report": "",
            "confidence": 0.0,
            "iteration": 1,
            "max_iterations": 3,
            "should_continue": True,
            "error": None,
        }
        
        result = await keeper_node(state)
        
        assert result["should_continue"] == True  # Should continue (not enough facts)
    
    @pytest.mark.asyncio
    async def test_keeper_node_stop(self):
        """Test keeper node decides to stop."""
        from services.orchestrator.core.graph import keeper_node, GraphState
        
        state: GraphState = {
            "job_id": "test-job",
            "query": "test",
            "path": "D",
            "status": "running",
            "sub_queries": [],
            "hypotheses": [],
            "facts": [{"entity": f"test{i}", "value": str(i)} for i in range(15)],  # 15 facts
            "sources": [],
            "artifacts": [],
            "generator_output": "",
            "critic_feedback": "",
            "judge_verdict": "",
            "report": "",
            "confidence": 0.0,
            "iteration": 2,
            "max_iterations": 3,
            "should_continue": True,
            "error": None,
        }
        
        result = await keeper_node(state)
        
        assert result["should_continue"] == False  # Should stop (enough facts)
    
    @pytest.mark.asyncio
    async def test_synthesizer_node(self):
        """Test synthesizer creates final report."""
        from services.orchestrator.core.graph import synthesizer_node, GraphState
        
        state: GraphState = {
            "job_id": "test-job",
            "query": "test query",
            "path": "D",
            "status": "running",
            "sub_queries": [],
            "hypotheses": [],
            "facts": [{"entity": "test", "value": "100"}],
            "sources": [{"url": "https://example.com", "title": "Example"}],
            "artifacts": [],
            "generator_output": "Test findings",
            "critic_feedback": "",
            "judge_verdict": "",
            "report": "",
            "confidence": 0.75,
            "iteration": 2,
            "max_iterations": 3,
            "should_continue": False,
            "error": None,
        }
        
        result = await synthesizer_node(state)
        
        assert result["report"] != ""
        assert "test query" in result["report"]
        assert result["status"] == "completed"


# ============================================================================
# MCP Orchestrator Tests
# ============================================================================

class TestMCPOrchestrator:
    """Tests for the MCP orchestrator client."""
    
    def test_orchestrator_init(self):
        """Test orchestrator initialization."""
        from services.orchestrator.mcp.client import MCPOrchestrator
        
        orchestrator = MCPOrchestrator()
        
        assert orchestrator.tools == []
        assert orchestrator.tool_names == []
    
    @pytest.mark.asyncio
    async def test_orchestrator_tool_not_found(self):
        """Test calling a non-existent tool."""
        from services.orchestrator.mcp.client import MCPOrchestrator
        
        orchestrator = MCPOrchestrator()
        result = await orchestrator.call_tool("nonexistent_tool", {})
        
        assert result.isError
        assert "not found" in result.content[0].text.lower()


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
