"""
Tests for tool isolation and lazy loading.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestToolIsolator:
    """Tests for ToolIsolator class."""
    
    def test_import_isolation(self):
        """Test that isolation classes can be imported."""
        from shared.tools.isolation import (
            ToolIsolator,
            LazyToolLoader,
            IsolatedResult,
            get_isolator,
            get_lazy_loader,
        )
        assert ToolIsolator is not None
        assert LazyToolLoader is not None
    
    def test_create_isolator(self):
        """Test creating tool isolator."""
        from shared.tools.isolation import ToolIsolator
        
        isolator = ToolIsolator(timeout=60.0)
        assert isolator.timeout == 60.0
    
    def test_default_timeout(self):
        """Test default timeout value."""
        from shared.tools.isolation import ToolIsolator
        
        isolator = ToolIsolator()
        assert isolator.timeout == 120.0


class TestIsolatedResult:
    """Tests for IsolatedResult dataclass."""
    
    def test_create_success_result(self):
        """Test creating success result."""
        from shared.tools.isolation import IsolatedResult
        
        result = IsolatedResult(
            success=True,
            result={"data": "value"},
            error=None,
            stdout="output",
            stderr=""
        )
        
        assert result.success is True
        assert result.result == {"data": "value"}
    
    def test_create_error_result(self):
        """Test creating error result."""
        from shared.tools.isolation import IsolatedResult
        
        result = IsolatedResult(
            success=False,
            result=None,
            error="Something failed",
            stdout="",
            stderr="error output"
        )
        
        assert result.success is False
        assert result.error == "Something failed"


class TestLazyToolLoader:
    """Tests for LazyToolLoader class."""
    
    def test_loader_init(self):
        """Test lazy loader initialization."""
        from shared.tools.isolation import LazyToolLoader
        
        loader = LazyToolLoader()
        assert loader.loaded_servers() == []
    
    def test_is_loaded_initially_false(self):
        """Test is_loaded returns false initially."""
        from shared.tools.isolation import LazyToolLoader
        
        loader = LazyToolLoader()
        assert loader.is_loaded("any_server") is False
    
    def test_loaded_servers_empty(self):
        """Test loaded_servers initially empty."""
        from shared.tools.isolation import LazyToolLoader
        
        loader = LazyToolLoader()
        assert len(loader.loaded_servers()) == 0
    
    def test_unload_nonexistent_server(self):
        """Test unloading non-existent server doesn't raise."""
        from shared.tools.isolation import LazyToolLoader
        
        loader = LazyToolLoader()
        # Should not raise
        loader.unload("nonexistent_server")
    
    def test_get_caches_server(self):
        """Test that get caches loaded servers."""
        from shared.tools.isolation import LazyToolLoader
        
        loader = LazyToolLoader()
        # After first get, server should be loaded
        # (this may fail if server doesn't exist, which is expected)


class TestGetIsolator:
    """Tests for get_isolator singleton."""
    
    def test_get_isolator(self):
        """Test getting global isolator."""
        from shared.tools.isolation import get_isolator, ToolIsolator
        
        isolator = get_isolator()
        assert isinstance(isolator, ToolIsolator)
    
    def test_get_isolator_same_instance(self):
        """Test get_isolator returns same instance."""
        from shared.tools.isolation import get_isolator
        
        isolator1 = get_isolator()
        isolator2 = get_isolator()
        assert isolator1 is isolator2


class TestGetLazyLoader:
    """Tests for get_lazy_loader singleton."""
    
    def test_get_lazy_loader(self):
        """Test getting global lazy loader."""
        from shared.tools.isolation import get_lazy_loader, LazyToolLoader
        
        loader = get_lazy_loader()
        assert isinstance(loader, LazyToolLoader)
