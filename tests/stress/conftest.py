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

API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://localhost:8000")
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8001")

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

    # Handle --quiet-stress
    if config.getoption("--quiet-stress"):
        noisy_loggers = [
            "shared.hardware.detector",
            "shared.logging.middleware",
            "services.client.runner",
            "uvicorn.access",
        ]
        
        # Set explicitly for current process
        for name in noisy_loggers:
            logging.getLogger(name).setLevel(logging.WARNING)
            
        # Set env var for subprocesses (API Gateway, etc.)
        os.environ["QUIET_LOGGERS"] = ",".join(noisy_loggers)

    
    # Register markers
    config.addinivalue_line("markers", "stress: Stress/load tests")


def pytest_addoption(parser):
    """Add custom pytest options for stress tests."""
    try:
        parser.addoption(
            "--query",
            action="store",
            default=None,
            help="Query ID(s) comma-separated (e.g., '1' or '1,2,3') OR a custom query string (e.g., 'Analyze AAPL stock')",
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

    try:
        parser.addoption(
            "--quiet-stress",
            action="store_true",
            default=False,
            help="Suppress noisy loggers during stress tests",
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

    def _log_request(self, method: str, path: str, kwargs: dict):
        """Log full request if verbose mode."""
        if os.getenv("KEA_LOG_NO_TRUNCATE") != "1":
            return
            
        print(f"\n⚡ REQUEST: {method} {path}")
        if "json" in kwargs:
            print(f"BODY: {kwargs['json']}")
        elif "data" in kwargs:
             print(f"DATA: {kwargs['data']}")
        elif "params" in kwargs:
             print(f"PARAMS: {kwargs['params']}")

    def _log_response(self, response: httpx.Response):
        """Log full response if verbose mode."""
        if os.getenv("KEA_LOG_NO_TRUNCATE") != "1":
            return
            
        print(f"⚡ RESPONSE: {response.status_code}")
        try:
            print(f"BODY: {response.json()}")
        except:
            print(f"BODY: {response.text}")
        print("")
    
    async def get(self, path: str, **kwargs) -> httpx.Response:
        """Make authenticated GET request."""
        self._log_request("GET", path, kwargs)
        response = await self._client.get(
            f"{self.base_url}{path}",
            headers=self.headers,
            **kwargs,
        )
        self._log_response(response)
        return response
    
    async def post(self, path: str, **kwargs) -> httpx.Response:
        """Make authenticated POST request."""
        self._log_request("POST", path, kwargs)
        response = await self._client.post(
            f"{self.base_url}{path}",
            headers=self.headers,
            **kwargs,
        )
        self._log_response(response)
        return response
    
    async def delete(self, path: str, **kwargs) -> httpx.Response:
        """Make authenticated DELETE request."""
        self._log_request("DELETE", path, kwargs)
        response = await self._client.delete(
            f"{self.base_url}{path}",
            headers=self.headers,
            **kwargs,
        )
        self._log_response(response)
        return response
    
    async def stream(self, method: str, path: str, **kwargs):
        """Make streaming request."""
        self._log_request(method, path, kwargs)
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

import subprocess
import time
import signal

# =============================================================================
# Service Lifecycle Management
# =============================================================================

async def wait_for_service(url: str, name: str, timeout: int = 30) -> bool:
    """Wait for a service to become healthy."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                resp = await client.get(f"{url}/health")
                if resp.status_code == 200:
                    logging.info(f"✅ {name} is READY at {url}")
                    return True
        except Exception:
            pass
        await asyncio.sleep(0.5)
        
    logging.error(f"❌ {name} failed to start at {url} within {timeout}s")
    return False

@pytest.fixture(scope="session", autouse=True)
async def bootstrap_services():
    """
    Ensure all microservices are running. 
    Auto-starts them as subprocesses if not detected.
    """
    # 1. Check if already running (e.g. Docker or manual)
    api_ok = await wait_for_service(API_GATEWAY_URL, "API Gateway", timeout=1)
    orch_ok = await wait_for_service(ORCHESTRATOR_URL, "Orchestrator", timeout=1)
    # RAG service URL assumption (usually 8003 based on plan)
    RAG_URL = "http://localhost:8003"
    rag_ok = await wait_for_service(RAG_URL, "RAG Service", timeout=1)

    procs = []

    # 2. Start missing services
    if not (api_ok and orch_ok and rag_ok):
        logging.info("🚀 Bootstrapping Microservices (Subprocesses)...")
        env = os.environ.copy()
        
        # Ensure Critical Env Vars
        if not env.get("DATABASE_URL"):
             logging.warning("⚠️ DATABASE_URL not set! Services might fail.")
        
        # Paths are relative to project root (cwd)
        # We assume pytest is run from project root
        
        # Start RAG Service (Port 8001)
        if not rag_ok:
            logging.info("   Starting RAG Service...")
            p_rag = subprocess.Popen(
                [sys.executable, "-m", "services.rag_service.main"],
                env=env,
                cwd=os.getcwd()
            )
            procs.append(p_rag)
        
        # Start Orchestrator (Port 8002 / 8000?)
        # Note: conftest says 8000, plan says 8002. Let's trust env or standard.
        # Docker compose says 8002 internal, mapped to 8002.
        # conftest defaults to 8000. Let's assume 8000 is strictly for orchestrator
        # BUT wait, the code says ORCHESTRATOR_URL defaults to http://localhost:8000
        # docker-compose maps 8002:8002.
        # Let's try to stick to what the code expects (8000) or update expectation.
        # Orchestrator main.py usually uses port defined in args or env.
        if not orch_ok:
            logging.info("   Starting Orchestrator...")
            p_orch = subprocess.Popen(
                [sys.executable, "-m", "services.orchestrator.main"],
                env=env,
                cwd=os.getcwd()
            )
            procs.append(p_orch)

        # Start API Gateway (Port 8080)
        if not api_ok:
            logging.info("   Starting API Gateway...")
            p_api = subprocess.Popen(
                [sys.executable, "-m", "services.api_gateway.main"],
                env=env,
                cwd=os.getcwd()
            )
            procs.append(p_api)
            
        # 3. Wait for startup
        logging.info("⏳ Waiting for services to come online...")
        # Give them a moment to crash or bind
        await asyncio.sleep(5) 
        
        ready = await asyncio.gather(
            wait_for_service(RAG_URL, "RAG Service"),
            wait_for_service(ORCHESTRATOR_URL, "Orchestrator"),
            wait_for_service(API_GATEWAY_URL, "API Gateway")
        )
        
        if not all(ready):
            logging.error("❌ Failed to verify all services. Tearing down...")
            for p in procs:
                p.terminate()
            pytest.fail("Could not bootstrap Kea microservices.")

    yield {"api_gateway": True, "custom_procs": len(procs) > 0}

    # 4. Teardown
    if procs:
        logging.info("🛑 Tearing down bootstrapped services...")
        for p in procs:
            if p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    p.kill()
        logging.info("✅ Services stopped.")

@pytest.fixture(scope="session")
def services_available(bootstrap_services):
    """Compatibility fixture."""
    return bootstrap_services


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
    """Get query IDs or custom query from command line or environment.
    
    Returns list of either:
    - int: predefined query ID
    - str: custom query string
    
    Priority:
    1. STRESS_TEST_QUERY environment variable (for Colab/Kaggle)
    2. --query command line argument
    3. Default to Query 1
    """
    import os
    
    # Priority 1: Environment variable (most reliable for Colab/Kaggle)
    env_query = os.getenv("STRESS_TEST_QUERY")
    if env_query:
        print(f"DEBUG: Using env var STRESS_TEST_QUERY = {env_query!r}")
        if env_query.replace(",", "").replace(" ", "").isdigit():
            return [int(q.strip()) for q in env_query.split(",")]
        else:
            return [env_query]
    
    # Priority 2: Command line argument  
    query_arg = request.config.getoption("--query", default=None)
    print(f"DEBUG: --query arg = {query_arg!r}")
    
    if query_arg:
        # Check if it looks like numeric ID(s)
        if query_arg.replace(",", "").replace(" ", "").isdigit():
            return [int(q.strip()) for q in query_arg.split(",")]
        else:
            # It's a custom query string
            return [query_arg]  # Return as single-item list of string
    
    return [1]  # Default to Query 1 (Indonesian Alpha Hunt)


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
def setup_stress_test_environment(monkeypatch, request):
    """
    Configure environment for stress testing.
    """
    # Enable stress test mode
    monkeypatch.setenv("STRESS_TEST_MODE", "1")
    
    # Set rate limiting
    monkeypatch.setenv("LLM_RATE_LIMIT_SECONDS", "3")

    # Check for verbosity (mapped to -v flag)
    # Note: request.config.getoption("verbose") returns int (0, 1, 2...)
    if request.config.getoption("verbose") > 0:
        monkeypatch.setenv("KEA_LOG_NO_TRUNCATE", "1")
