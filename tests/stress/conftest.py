"""
Stress Test Fixtures.

Pytest fixtures and configuration for stress testing Kea.
Includes API client with authentication support.
"""

import pytest
import asyncio
import logging
import os
import sys

import httpx

from tests.stress.metrics import MetricsCollector
from tests.stress.queries import QUERIES, get_query


# =============================================================================
# API Configuration
# =============================================================================

API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://localhost:8080")
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")

# Test user credentials (will be created if not exists)
TEST_USER_EMAIL = "stress_test@example.com"
TEST_USER_PASSWORD = "stress_test_password_123"
TEST_USER_NAME = "Stress Test User"


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
# API Authentication Fixtures
# =============================================================================

class AuthenticatedAPIClient:
    """
    HTTP client with automatic authentication.
    
    Handles JWT token management for stress test API calls.
    """
    
    def __init__(self, base_url: str = API_GATEWAY_URL):
        self.base_url = base_url
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self.user_id: str | None = None
        self._client: httpx.AsyncClient | None = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def initialize(self):
        """Initialize HTTP client and authenticate."""
        self._client = httpx.AsyncClient(timeout=300.0)
        await self._authenticate()
    
    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def _authenticate(self):
        """
        Authenticate with test user credentials.
        
        Attempts login first; if user doesn't exist, registers.
        """
        # Try login first
        try:
            response = await self._client.post(
                f"{self.base_url}/api/v1/auth/login",
                json={
                    "email": TEST_USER_EMAIL,
                    "password": TEST_USER_PASSWORD,
                },
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.refresh_token = data["refresh_token"]
                self.user_id = data["user"]["user_id"]
                return
        except Exception:
            pass
        
        # If login fails, register new user
        response = await self._client.post(
            f"{self.base_url}/api/v1/auth/register",
            json={
                "email": TEST_USER_EMAIL,
                "name": TEST_USER_NAME,
                "password": TEST_USER_PASSWORD,
            },
        )
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]
            self.user_id = data["user"]["user_id"]
        else:
            raise Exception(f"Failed to authenticate: {response.text}")
    
    @property
    def headers(self) -> dict:
        """Get headers with authorization."""
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers
    
    async def get(self, path: str, **kwargs) -> httpx.Response:
        """Make authenticated GET request."""
        return await self._client.get(
            f"{self.base_url}{path}",
            headers=self.headers,
            **kwargs,
        )
    
    async def post(self, path: str, **kwargs) -> httpx.Response:
        """Make authenticated POST request."""
        return await self._client.post(
            f"{self.base_url}{path}",
            headers=self.headers,
            **kwargs,
        )
    
    async def delete(self, path: str, **kwargs) -> httpx.Response:
        """Make authenticated DELETE request."""
        return await self._client.delete(
            f"{self.base_url}{path}",
            headers=self.headers,
            **kwargs,
        )
    
    async def stream(self, method: str, path: str, **kwargs):
        """Make streaming request."""
        return self._client.stream(
            method,
            f"{self.base_url}{path}",
            headers=self.headers,
            **kwargs,
        )


@pytest.fixture
async def api_client():
    """
    Function-scoped authenticated API client.
    
    Creates fresh client per test to avoid event loop issues.
    """
    client = AuthenticatedAPIClient()
    await client.initialize()
    yield client
    await client.close()


@pytest.fixture
async def fresh_api_client():
    """
    Function-scoped authenticated API client.
    
    Creates fresh client for each test.
    """
    async with AuthenticatedAPIClient() as client:
        yield client


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


# =============================================================================
# Service Check Fixtures
# =============================================================================

async def check_service(url: str) -> bool:
    """Check if a service is available."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{url}/health")
            return resp.status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="session")
async def services_available():
    """Check that all required services are running."""
    api_ok = await check_service(API_GATEWAY_URL)
    orch_ok = await check_service(ORCHESTRATOR_URL)
    
    if not api_ok:
        pytest.skip(f"API Gateway not running at {API_GATEWAY_URL}")
    if not orch_ok:
        pytest.skip(f"Orchestrator not running at {ORCHESTRATOR_URL}")
    
    return {"api_gateway": api_ok, "orchestrator": orch_ok}


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
