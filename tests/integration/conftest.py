"""
Integration Tests: Common utilities.

Shared fixtures and helpers for integration tests.
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


def skip_if_api_gateway_down(url: str = API_GATEWAY_URL):
    """Skip test if API Gateway not running."""
    import asyncio
    
    async def _check():
        return await check_service(url)
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Can't run nested event loop, assume available
            return
    except RuntimeError:
        pass
    
    if not asyncio.run(_check()):
        pytest.skip(f"API Gateway not running at {url}")


def skip_if_orchestrator_down(url: str = ORCHESTRATOR_URL):
    """Skip test if Orchestrator not running."""
    import asyncio
    
    async def _check():
        return await check_service(url)
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return
    except RuntimeError:
        pass
    
    if not asyncio.run(_check()):
        pytest.skip(f"Orchestrator not running at {url}")


def skip_if_rag_service_down(url: str = RAG_SERVICE_URL):
    """Skip test if RAG Service not running."""
    import asyncio
    
    async def _check():
        return await check_service(url)
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return
    except RuntimeError:
        pass
    
    if not asyncio.run(_check()):
        pytest.skip(f"RAG Service not running at {url}")
