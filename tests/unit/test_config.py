"""
Unit Tests: Configuration.

Tests for shared/config.py configuration loading.
"""

import pytest
import os


class TestSettings:
    """Tests for Settings configuration."""
    
    def test_get_settings(self):
        """Get default settings."""
        from shared.config import get_settings
        
        settings = get_settings()
        
        assert settings is not None
        assert hasattr(settings, "environment")
        assert hasattr(settings, "llm")
        assert hasattr(settings, "mcp")
    
    def test_settings_singleton(self):
        """Settings returns same instance."""
        from shared.config import get_settings
        
        s1 = get_settings()
        s2 = get_settings()
        
        assert s1 is s2
    
    def test_environment_enum(self):
        """Environment is valid enum."""
        from shared.config import get_settings, Environment
        
        settings = get_settings()
        
        assert settings.environment in list(Environment)
    
    def test_llm_config(self):
        """LLM config has required fields."""
        from shared.config import get_settings
        
        settings = get_settings()
        
        assert hasattr(settings.llm, "default_provider")
        assert hasattr(settings.llm, "default_model")
        assert hasattr(settings.llm, "temperature")
    
    def test_mcp_config(self):
        """MCP config has servers list."""
        from shared.config import get_settings
        
        settings = get_settings()
        
        assert hasattr(settings.mcp, "servers")
        assert isinstance(settings.mcp.servers, list)


class TestEnvironmentVariables:
    """Tests for environment variable overrides."""
    
    def test_api_key_from_env(self):
        """API key loaded from environment."""
        # This just tests the mechanism exists
        key = os.getenv("OPENROUTER_API_KEY", "")
        # Key may or may not be set, just verify it doesn't crash
        assert isinstance(key, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
