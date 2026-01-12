"""
Integration Tests: Common utilities.

Shared fixtures and helpers for integration tests.
These tests require running services.
"""

import pytest
import httpx


# Service URLs
API_GATEWAY_URL = "http://localhost:8080"
ORCHESTRATOR_URL = "http://localhost:8000"
RAG_SERVICE_URL = "http://localhost:8001"


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
