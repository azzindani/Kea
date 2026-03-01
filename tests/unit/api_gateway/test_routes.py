"""
Unit Tests: API Gateway Routes.

Tests for services/api_gateway/routes/*.py
"""

import pytest


class TestJobsRoute:
    """Tests for jobs route."""

    def test_router_exists(self):
        """Jobs router exists."""
        from services.api_gateway.routes.jobs import router

        assert router is not None
        print(f"\n📍 Jobs routes: {len(router.routes)}")

    def test_router_has_endpoints(self):
        """Jobs router has endpoints."""
        from services.api_gateway.routes.jobs import router

        assert len(router.routes) > 0
        for route in router.routes:
            if hasattr(route, 'path'):
                print(f"   {route.methods} {route.path}")


class TestMemoryRoute:
    """Tests for memory route."""

    def test_router_exists(self):
        """Memory router exists."""
        from services.api_gateway.routes.memory import router

        assert router is not None

    def test_router_has_endpoints(self):
        """Memory router has endpoints."""
        from services.api_gateway.routes.memory import router

        assert len(router.routes) > 0


class TestArtifactsRoute:
    """Tests for artifacts route."""

    def test_router_exists(self):
        """Artifacts router exists."""
        from services.api_gateway.routes.artifacts import router

        assert router is not None


class TestGraphRoute:
    """Tests for graph route."""

    def test_router_exists(self):
        """Graph router exists."""
        from services.api_gateway.routes.graph import router

        assert router is not None


class TestInterventionsRoute:
    """Tests for interventions route."""

    def test_router_exists(self):
        """Interventions router exists."""
        from services.api_gateway.routes.interventions import router

        assert router is not None


class TestSystemRoute:
    """Tests for system route."""

    def test_router_exists(self):
        """System router exists."""
        from services.api_gateway.routes.system import router

        assert router is not None


class TestLLMRoute:
    """Tests for LLM route."""

    def test_router_exists(self):
        """LLM router exists."""
        from services.api_gateway.routes.llm import router

        assert router is not None


class TestMCPRoute:
    """Tests for MCP route."""

    def test_router_exists(self):
        """MCP router exists."""
        from services.api_gateway.routes.mcp import router

        assert router is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
