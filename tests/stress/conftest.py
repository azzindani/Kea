"""
Stress Test Fixtures.

Pytest fixtures and configuration for stress testing Kea.
"""

import pytest
import asyncio
import logging
import os
import sys

from tests.stress.metrics import MetricsCollector
from tests.stress.queries import QUERIES, get_query


# =============================================================================
# Pytest Plugin: Configuration
# =============================================================================

def pytest_configure(config):
    """Configure pytest for stress tests."""
    # Setup Kea logging with console format for readable output
    from shared.logging import setup_logging, LogConfig
    from shared.logging.structured import LogLevel
    
    # Use console format (not JSON) for test readability
    log_config = LogConfig(
        level=LogLevel.DEBUG,
        format="console",
        service_name="stress-test",
    )
    setup_logging(log_config)
    
    # Ensure root logger is at DEBUG level
    logging.getLogger().setLevel(logging.DEBUG)
    
    # Make sure stress test logger outputs everything
    logging.getLogger("tests.stress").setLevel(logging.DEBUG)
    
    # Register markers
    config.addinivalue_line("markers", "stress: Stress/load tests")


def pytest_addoption(parser):
    """Add custom pytest options for stress tests."""
    try:
        parser.addoption(
            "--query",
            action="store",
            default=None,
            help="Query ID(s) to run, comma-separated (e.g., '1' or '1,2,3')",
        )
    except ValueError:
        pass
    
    try:
        parser.addoption(
            "--output-dir",
            action="store",
            default="tests/stress/results",
            help="Output directory for results",
        )
    except ValueError:
        pass


# =============================================================================
# Session-scoped Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def hardware_profile():
    """Detect and return hardware profile for the test session."""
    from shared.hardware.detector import detect_hardware
    return detect_hardware()


@pytest.fixture(scope="session")
def llm_provider():
    """
    Initialize OpenRouter provider for stress tests.
    
    Uses nvidia/nemotron-3-nano-30b-a3b:free model.
    """
    from shared.llm.openrouter import OpenRouterProvider
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")
    
    return OpenRouterProvider(api_key=api_key)


@pytest.fixture(scope="session")
async def research_pipeline(hardware_profile):
    """
    Initialize research pipeline for stress tests.
    
    May fail on constrained hardware.
    """
    try:
        from services.orchestrator.core.pipeline import get_research_pipeline
        pipeline = get_research_pipeline()
        await pipeline.initialize()
        yield pipeline
    except Exception as e:
        pytest.skip(f"Pipeline not available: {e}")


# =============================================================================
# Function-scoped Fixtures
# =============================================================================

@pytest.fixture
def metrics_collector():
    """Fresh metrics collector for each test."""
    return MetricsCollector()


@pytest.fixture
def sample_query():
    """Get query 1 (Indonesian Alpha Hunt) for testing."""
    return get_query(1)


@pytest.fixture
def all_queries():
    """Get all stress test queries."""
    return QUERIES


@pytest.fixture
def query_ids(request):
    """Get query IDs from command line."""
    query_arg = request.config.getoption("--query", default=None)
    if query_arg:
        return [int(q.strip()) for q in query_arg.split(",")]
    return [1]  # Default to query 1


# =============================================================================
# Cleanup
# =============================================================================

@pytest.fixture(autouse=True)
async def cleanup_after_test():
    """Cleanup resources after each test."""
    yield
    
    # Force garbage collection
    import gc
    gc.collect()


# =============================================================================
# Environment Setup
# =============================================================================

@pytest.fixture(autouse=True)
def setup_stress_test_environment(monkeypatch):
    """
    Configure environment for stress testing.
    """
    # Enable stress test mode
    monkeypatch.setenv("STRESS_TEST_MODE", "1")
    
    # Set rate limiting
    monkeypatch.setenv("LLM_RATE_LIMIT_SECONDS", "3")
