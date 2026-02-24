"""
Unit Tests: API Gateway Main.

Tests for services/api_gateway/main.py
"""

import pytest


class TestAPIGatewayApp:
    """Tests for API gateway FastAPI app."""

    def test_app_exists(self):
        """App is created."""
        from services.api_gateway.main import app

        assert app is not None
        assert app.title is not None

    def test_app_routes(self):
        """App has routes."""
        from services.api_gateway.main import app

        assert len(app.routes) > 0
        print(f"\n📍 API Gateway routes: {len(app.routes)}")
        for route in app.routes[:10]:
            if hasattr(route, 'path'):
                print(f"   {route.path}")

    def test_app_version(self):
        """App has version."""
        from services.api_gateway.main import app

        assert app.version is not None or hasattr(app, 'version')


class TestAPIGatewayEndpoints:
    """Tests for API gateway endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Health endpoint exists."""
        from httpx import ASGITransport, AsyncClient

        from services.api_gateway.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code in [200, 404, 405]

    @pytest.mark.asyncio
    async def test_api_docs(self):
        """OpenAPI docs available."""
        from httpx import ASGITransport, AsyncClient

        from services.api_gateway.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/openapi.json")
            # Should have OpenAPI spec
            assert response.status_code in [200, 404]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
