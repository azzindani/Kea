# Test fixtures and configuration
import pytest
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_fact():
    """Sample atomic fact for testing."""
    return {
        "entity": "Test Entity",
        "attribute": "test_attribute",
        "value": "100",
        "unit": "units",
        "source_url": "https://example.com/test",
        "confidence_score": 0.85,
    }


@pytest.fixture
def sample_research_state():
    """Sample research state for testing."""
    return {
        "job_id": "test-job-123",
        "query": "Test research query",
        "path": "D",
        "status": "running",
        "sub_queries": ["sub-query-1", "sub-query-2"],
        "hypotheses": ["hypothesis-1"],
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


@pytest.fixture
def mock_tool_result():
    """Mock MCP tool result."""
    from shared.mcp.protocol import ToolResult, TextContent
    
    return ToolResult(
        content=[TextContent(text="Mock tool result")],
        isError=False,
    )
