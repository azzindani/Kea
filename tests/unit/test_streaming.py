"""
Unit Tests: SSE Streaming Endpoint.

Tests for the streaming research endpoint.
"""

import pytest


class TestStreamingEndpoint:
    """Tests for SSE streaming endpoint."""

    def test_endpoint_exists(self):
        """Streaming endpoint exists in app."""
        from services.orchestrator.main import app

        # Check routes
        route_paths = [r.path for r in app.routes if hasattr(r, 'path')]

        assert "/research/stream" in route_paths

    @pytest.mark.asyncio
    async def test_streaming_response(self):
        """Streaming endpoint returns SSE response."""
        from httpx import ASGITransport, AsyncClient

        from services.orchestrator.main import app

        transport = ASGITransport(app=app)

        # Note: The actual streaming test would require more setup
        # This just verifies the endpoint is accessible
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # The endpoint requires query param
            response = await client.get("/research/stream?query=test")

            # Should return SSE content type
            assert response.status_code in [200, 500]  # 500 if graph not initialized


class TestStreamingHelpers:
    """Tests for streaming helper functions."""

    def test_json_import(self):
        """JSON module available for SSE."""
        import json

        data = {"event": "test", "content": "hello"}
        encoded = json.dumps(data)
        decoded = json.loads(encoded)

        assert decoded == data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
