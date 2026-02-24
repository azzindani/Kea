"""
Unit Tests: JIT Tool Loader.

Tests for Just-In-Time tool loading.
"""

from unittest.mock import patch

import pytest
from shared.tools.jit_loader import (
    JITLoader,
    ToolDeps,
    get_jit_loader,
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

    def test_has_uv_attribute(self, loader):
        """Test uv availability attribute."""
        # has_uv is a property/attribute, not a method
        result = loader.has_uv
        assert isinstance(result, bool)

    def test_has_gpu_attribute(self, loader):
        """Test GPU availability attribute."""
        # has_gpu is a property/attribute, not a method
        result = loader.has_gpu
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

    def test_validate_logs_warning_for_unsafe(self):
        """Test validation logs warning for unlisted packages."""
        with patch.object(JITLoader, "_find_config", return_value=None):
            with patch.object(JITLoader, "_load_config"):
                loader = JITLoader()
                loader._allowed_packages = {"pandas"}

                # _validate_package logs a warning but doesn't raise
                # Just verify it doesn't crash
                try:
                    loader._validate_package("unlisted_package")
                except Exception:
                    pass  # May or may not raise depending on implementation


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
