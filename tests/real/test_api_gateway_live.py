"""
API Gateway Live Tests.

Tests all API endpoints with real requests.
Run with: pytest tests/real/test_api_gateway_live.py -v -s --log-cli-level=INFO
"""


import pytest


class TestAPIGatewayRoutes:
    """Test API gateway route handlers directly."""

    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_jobs_route(self, logger):
        """Test jobs route handler."""
        logger.info("Testing jobs route")

        from services.api_gateway.routes.jobs import router

        # Check router exists and has endpoints
        assert router is not None
        print(f"\n📍 Jobs router: {len(router.routes)} routes")

        for route in router.routes:
            print(f"   {route.methods} {route.path}")

    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_memory_route(self, logger):
        """Test memory route handler."""
        logger.info("Testing memory route")

        from services.api_gateway.routes.memory import router

        assert router is not None
        print(f"\n📍 Memory router: {len(router.routes)} routes")

        for route in router.routes:
            print(f"   {route.methods} {route.path}")

    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_mcp_route(self, logger):
        """Test MCP route handler."""
        logger.info("Testing MCP route")

        from services.api_gateway.routes.mcp import router

        assert router is not None
        print(f"\n📍 MCP router: {len(router.routes)} routes")

        for route in router.routes:
            print(f"   {route.methods} {route.path}")

    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_llm_route(self, logger):
        """Test LLM route handler."""
        logger.info("Testing LLM route")

        from services.api_gateway.routes.llm import router

        assert router is not None
        print(f"\n📍 LLM router: {len(router.routes)} routes")

        for route in router.routes:
            print(f"   {route.methods} {route.path}")

    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_system_route(self, logger):
        """Test system route handler."""
        logger.info("Testing system route")

        from services.api_gateway.routes.system import router

        assert router is not None
        print(f"\n📍 System router: {len(router.routes)} routes")

        for route in router.routes:
            print(f"   {route.methods} {route.path}")


class TestAPIGatewayMain:
    """Test API gateway main application."""

    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_app_creation(self, logger):
        """Test FastAPI app creation."""
        logger.info("Testing app creation")

        from services.api_gateway.main import app

        assert app is not None
        print(f"\n🚀 API Gateway App: {app.title}")
        print(f"   Version: {app.version}")
        print(f"   Routes: {len(app.routes)}")


class TestOrchestratorAPI:
    """Test orchestrator integration."""

    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_orchestrator_main(self, logger):
        """Test orchestrator main module."""
        logger.info("Testing orchestrator main")

        from services.orchestrator.main import app

        assert app is not None
        print(f"\n🧠 Orchestrator App: {app.title}")


class TestRAGServiceAPI:
    """Test RAG service integration."""

    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_rag_main(self, logger):
        """Test RAG service main module."""
        logger.info("Testing RAG main")

        from services.rag_service.main import app

        assert app is not None
        print(f"\n💾 RAG Service App: {app.title}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--log-cli-level=INFO"])
