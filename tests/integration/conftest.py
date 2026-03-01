"""
Integration Tests: Common utilities.

Shared fixtures and helpers for integration tests.
These tests require running services.
"""

import httpx
import pytest

from shared.config import get_settings

settings = get_settings()

# Service URLs from central config
API_GATEWAY_URL = settings.services.gateway
ORCHESTRATOR_URL = settings.services.orchestrator
RAG_SERVICE_URL = settings.services.rag_service

# Test user credentials
TEST_USER_EMAIL = "integration_test@example.com"
TEST_USER_PASSWORD = "integration_test_password_123"
TEST_USER_NAME = "Integration Test User"


async def check_service(url: str) -> bool:
    """Check if a service is available."""
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            resp = await client.get(f"{url}/health")
            return resp.status_code == 200
    except Exception:
        return False


async def check_api_gateway() -> bool:
    """Check if API Gateway is available."""
    return await check_service(API_GATEWAY_URL)


async def check_orchestrator() -> bool:
    """Check if Orchestrator is available."""
    return await check_service(ORCHESTRATOR_URL)


async def check_rag_service() -> bool:
    """Check if RAG Service is available."""
    return await check_service(RAG_SERVICE_URL)


# ============================================================================
# Authenticated API Client
# ============================================================================

class AuthenticatedClient:
    """
    HTTP client with automatic authentication for integration tests.
    """

    def __init__(self, base_url: str = API_GATEWAY_URL):
        self.base_url = base_url
        self.access_token: str | None = None
        self.user_id: str | None = None
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def initialize(self):
        """Initialize and authenticate."""
        self._client = httpx.AsyncClient(timeout=30.0)
        await self._authenticate()

    async def close(self):
        """Close client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _authenticate(self):
        """Register or login test user."""
        # Try login first
        try:
            response = await self._client.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD},
            )
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.user_id = data["user"]["user_id"]
                return
        except Exception:
            pass

        # Register if login fails
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
            self.user_id = data["user"]["user_id"]
        else:
            # If auth fails, tests will run without auth (some endpoints don't need it)
            self.access_token = None
            self.user_id = None

    @property
    def headers(self) -> dict:
        """Get auth headers."""
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    async def get(self, path: str, **kwargs) -> httpx.Response:
        """Authenticated GET."""
        return await self._client.get(f"{self.base_url}{path}", headers=self.headers, **kwargs)

    async def post(self, path: str, **kwargs) -> httpx.Response:
        """Authenticated POST."""
        return await self._client.post(f"{self.base_url}{path}", headers=self.headers, **kwargs)

    async def put(self, path: str, **kwargs) -> httpx.Response:
        """Authenticated PUT."""
        return await self._client.put(f"{self.base_url}{path}", headers=self.headers, **kwargs)

    async def delete(self, path: str, **kwargs) -> httpx.Response:
        """Authenticated DELETE."""
        return await self._client.delete(f"{self.base_url}{path}", headers=self.headers, **kwargs)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="module")
def api_gateway_url():
    """Get API Gateway URL."""
    return API_GATEWAY_URL


@pytest.fixture(scope="module")
def orchestrator_url():
    """Get Orchestrator URL."""
    return ORCHESTRATOR_URL


@pytest.fixture(scope="module")
def rag_service_url():
    """Get RAG Service URL."""
    return RAG_SERVICE_URL


@pytest.fixture
async def auth_client():
    """
    Function-scoped authenticated API client.
    
    Creates fresh client per test to avoid event loop issues.
    """
    client = AuthenticatedClient()
    await client.initialize()
    yield client
    await client.close()


@pytest.fixture(autouse=True)
async def skip_if_service_unavailable(request):
    """
    Auto-skip tests if required service is not available.
    
    Looks at the test module name to determine which service to check:
    - test_*_api.py, test_e2e.py -> API Gateway (8080)
    - test_pipeline.py -> Check based on class name
    - test_api_health.py -> Already handled per-test
    """
    # Get the test file name
    test_file = request.fspath.basename
    test_class = request.node.parent.name if request.node.parent else ""

    # Skip rules based on test file
    if test_file in [
        "test_artifacts_api.py",
        "test_e2e.py",
        "test_graph_api.py",
        "test_interventions_api.py",
        "test_jobs_api.py",
        "test_llm_api.py",
        "test_mcp_api.py",
        "test_memory_api.py",
        "test_system_api.py",
    ]:
        # These require API Gateway
        if not await check_api_gateway():
            pytest.skip(f"API Gateway not running at {API_GATEWAY_URL}")

    elif test_file == "test_pipeline.py":
        # Pipeline tests - check based on class name
        if "APIGateway" in test_class:
            if not await check_api_gateway():
                pytest.skip(f"API Gateway not running at {API_GATEWAY_URL}")
        elif "RAGService" in test_class:
            if not await check_rag_service():
                pytest.skip(f"RAG Service not running at {RAG_SERVICE_URL}")
        elif "Orchestrator" in test_class:
            if not await check_orchestrator():
                pytest.skip(f"Orchestrator not running at {ORCHESTRATOR_URL}")
        elif "FullPipeline" in test_class:
            # Full pipeline needs all services
            if not await check_api_gateway():
                pytest.skip(f"API Gateway not running at {API_GATEWAY_URL}")
