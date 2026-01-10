"""
Test Fixtures and Configuration.

Shared fixtures for all tests.
"""

import pytest
import asyncio
import os


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests (no API required)")
    config.addinivalue_line("markers", "integration: Integration tests (API required)")
    config.addinivalue_line("markers", "mcp: MCP tool tests (API required)")
    config.addinivalue_line("markers", "stress: Stress/load tests")
    config.addinivalue_line("markers", "slow: Slow-running tests")


# ============================================================================
# Event Loop Fixture
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# API URL Fixtures
# ============================================================================

@pytest.fixture
def api_gateway_url():
    """API Gateway base URL."""
    return os.getenv("API_GATEWAY_URL", "http://localhost:8080")


@pytest.fixture
def orchestrator_url():
    """Orchestrator service URL."""
    return os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")


@pytest.fixture
def rag_service_url():
    """RAG service URL."""
    return os.getenv("RAG_SERVICE_URL", "http://localhost:8001")


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_fact():
    """Sample atomic fact for testing."""
    from shared.schemas import AtomicFact
    from datetime import datetime
    
    return AtomicFact(
        fact_id="test-fact-001",
        entity="Test Entity",
        attribute="test_attribute",
        value="100",
        unit="units",
        source_url="https://example.com/test",
        source_title="Test Source",
        confidence_score=0.85,
        extracted_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_job_request():
    """Sample job request for testing."""
    return {
        "query": "Test research query",
        "job_type": "deep_research",
        "depth": 2,
        "max_sources": 10,
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


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_tool_result():
    """Mock MCP tool result."""
    from shared.mcp.protocol import ToolResult, TextContent
    
    return ToolResult(
        content=[TextContent(text="Mock tool result")],
        isError=False,
    )


@pytest.fixture
def mock_error_result():
    """Mock MCP error result."""
    from shared.mcp.protocol import ToolResult, TextContent
    
    return ToolResult(
        content=[TextContent(text="Error: Test error")],
        isError=True,
    )


# ============================================================================
# HTTP Client Fixture
# ============================================================================

@pytest.fixture
async def http_client():
    """Async HTTP client for tests."""
    import httpx
    
    async with httpx.AsyncClient(timeout=30) as client:
        yield client
