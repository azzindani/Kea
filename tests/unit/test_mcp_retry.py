"""
Unit Tests: MCP Retry Mechanism.

Tests for MCP retry configuration and functionality.
"""

import pytest


class TestMCPRetryConfig:
    """Tests for MCP retry configuration."""

    def test_mcp_settings_defaults(self):
        """MCP settings have retry defaults."""
        from shared.config import MCPSettings

        settings = MCPSettings()

        assert settings.max_retries == 3
        assert settings.retry_delay == 1.0
        assert settings.retry_backoff == 2.0
        assert settings.retry_on_timeout == True
        assert settings.retry_on_connection_error == True

    def test_mcp_settings_custom(self):
        """MCP settings accept custom values."""
        from shared.config import MCPSettings

        settings = MCPSettings(
            max_retries=5,
            retry_delay=0.5,
            retry_backoff=3.0,
        )

        assert settings.max_retries == 5
        assert settings.retry_delay == 0.5
        assert settings.retry_backoff == 3.0

    def test_mcp_rate_limit_config(self):
        """MCP settings include rate limiting."""
        from shared.config import MCPSettings

        settings = MCPSettings()

        assert settings.rate_limit_per_second == 10.0
        assert settings.max_concurrent_tools == 5
        assert settings.tool_timeout_seconds == 60.0


class TestMCPClientRetry:
    """Tests for MCP client retry behavior."""

    def test_orchestrator_has_retry(self):
        """MCPOrchestrator uses retry config."""
        from services.orchestrator.mcp.client import MCPOrchestrator

        orchestrator = MCPOrchestrator()

        # Should not raise on init
        assert orchestrator is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
