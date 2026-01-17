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


# ============================================================================
# Database Isolation Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """
    Set up test environment variables for proper PostgreSQL isolation.
    """
    # Set environment to development mode (test mode works but dev is more permissive)
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("TEST_MODE", "1")
    
    # Disable external services that may not be available in test environment
    if not os.getenv("QDRANT_URL"):
        monkeypatch.setenv("QDRANT_URL", "")
    if not os.getenv("REDIS_URL"):
        monkeypatch.setenv("REDIS_URL", "")


@pytest.fixture(autouse=True)
def reset_singleton_managers():
    """
    Reset singleton manager instances between tests to avoid state leakage.
    """
    yield
    
    # Reset singletons after each test
    import shared.users.manager as user_mgr
    import shared.conversations.manager as conv_mgr
    
    user_mgr._user_manager = None
    user_mgr._api_key_manager = None
    conv_mgr._conversation_manager = None


@pytest.fixture(scope="function")
async def db_session():
    """
    Provide an isolated database session for tests that need direct DB access.
    
    Uses savepoints to rollback after each test.
    """
    from shared.database.connection import get_database_pool
    
    pool = await get_database_pool()
    
    async with pool.acquire() as conn:
        # Start a transaction
        tr = conn.transaction()
        await tr.start()
        
        try:
            yield conn
        finally:
            # Rollback to clean up test data
            await tr.rollback()


@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio backend for anyio."""
    return "asyncio"


@pytest.fixture(scope="session")
async def shared_db_pool():
    """
    Session-scoped database pool for tests.
    
    This creates a single pool for the entire test session,
    avoiding repeated pool creation/destruction overhead.
    """
    from shared.database.connection import DatabasePool, DatabaseConfig
    import os
    
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        # No PostgreSQL configured, skip pool creation
        yield None
        return
    
    config = DatabaseConfig(
        url=db_url,
        min_connections=5,
        max_connections=20,
    )
    pool = DatabasePool(config)
    await pool.initialize()
    
    yield pool
    
    await pool.close()
