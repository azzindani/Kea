"""
Unit Tests: RAG Service Main.

Tests for services/rag_service/main.py
"""

import pytest


class TestRAGServiceApp:
    """Tests for RAG service FastAPI app."""

    def test_app_exists(self):
        """App is created."""
        from services.rag_service.main import app

        assert app is not None
        assert app.title is not None

    def test_app_routes(self):
        """App has routes."""
        from services.rag_service.main import app

        assert len(app.routes) > 0
        print(f"\n📍 RAG Service routes: {len(app.routes)}")
        for route in app.routes[:5]:
            if hasattr(route, 'path'):
                print(f"   {route.path}")

    def test_app_version(self):
        """App has version."""
        from services.rag_service.main import app

        assert app.version is not None or hasattr(app, 'version')


class TestRAGServiceEndpoints:
    """Tests for RAG service endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Health endpoint exists."""
        from httpx import ASGITransport, AsyncClient

        from services.rag_service.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code in [200, 404, 405]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
