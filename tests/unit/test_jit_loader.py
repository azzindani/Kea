"""
Unit Tests: JIT Tool Loader.

Tests for Just-In-Time tool loading.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from shared.tools.jit_loader import (
    JITLoader,
    ToolDeps,
    get_jit_loader,
    ensure_tool,
)


class TestJITLoader:
    """Test JITLoader class."""
    
    @pytest.fixture
    def loader(self):
        """Create loader for testing."""
        with patch.object(JITLoader, "_find_config", return_value=None):
            with patch.object(JITLoader, "_load_config"):
                return JITLoader()
    
    def test_loader_init(self, loader):
        """Test loader initialization."""
        assert hasattr(loader, "_installed")
    
    def test_has_uv_check(self, loader):
        """Test uv availability check."""
        result = loader.has_uv()
        assert isinstance(result, bool)
    
    def test_has_gpu_check(self, loader):
        """Test GPU availability check."""
        result = loader.has_gpu()
        assert isinstance(result, bool)
    
    def test_is_installed(self, loader):
        """Test package installed check."""
        # json is always installed
        result = loader.is_installed("json")
        assert isinstance(result, bool)


class TestToolDeps:
    """Test ToolDeps dataclass."""
    
    def test_default_deps(self):
        """Test default dependency values."""
        deps = ToolDeps()
        
        assert deps.packages == []
        assert deps.optional == []
        assert deps.gpu_packages == []
        assert deps.heavy is False
    
    def test_custom_deps(self):
        """Test custom dependencies."""
        deps = ToolDeps(
            packages=["pandas", "numpy"],
            optional=["matplotlib"],
            heavy=True,
        )
        
        assert len(deps.packages) == 2
        assert deps.heavy is True


class TestJITLoaderSecurity:
    """Test JIT loader security features."""
    
    def test_validate_safe_package(self):
        """Test validation of safe package names."""
        with patch.object(JITLoader, "_find_config", return_value=None):
            with patch.object(JITLoader, "_load_config"):
                loader = JITLoader()
                loader._allowed_packages = {"pandas", "numpy"}
                
                # Should not raise for allowed packages
                loader._validate_package("pandas")
    
    def test_validate_unsafe_package(self):
        """Test validation rejects unsafe packages."""
        with patch.object(JITLoader, "_find_config", return_value=None):
            with patch.object(JITLoader, "_load_config"):
                loader = JITLoader()
                loader._allowed_packages = {"pandas"}
                
                with pytest.raises(ValueError):
                    loader._validate_package("malicious; rm -rf /")


class TestGlobalJITLoader:
    """Test global JIT loader instance."""
    
    def test_get_jit_loader_returns_loader(self):
        """Test get_jit_loader returns JITLoader."""
        with patch.object(JITLoader, "_find_config", return_value=None):
            with patch.object(JITLoader, "_load_config"):
                import shared.tools.jit_loader as module
                module._loader = None  # Reset
                
                loader = get_jit_loader()
                
                assert isinstance(loader, JITLoader)
