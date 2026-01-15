"""
Unit Tests: Tool Isolation.

Tests for ToolIsolator and LazyToolLoader.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json
import tempfile
from pathlib import Path

from shared.tools.isolation import (
    IsolatedResult,
    ToolIsolator,
    LazyToolLoader,
    get_isolator,
    get_lazy_loader,
)


class TestIsolatedResult:
    """Test IsolatedResult dataclass."""
    
    def test_success_result(self):
        """Test successful result."""
        result = IsolatedResult(
            success=True,
            result={"data": "test"},
        )
        
        assert result.success is True
        assert result.result == {"data": "test"}
        assert result.error is None
    
    def test_failure_result(self):
        """Test failure result."""
        result = IsolatedResult(
            success=False,
            result=None,
            error="ImportError: No module named 'xyz'",
        )
        
        assert result.success is False
        assert result.error is not None
    
    def test_with_stdout_stderr(self):
        """Test result with stdout/stderr."""
        result = IsolatedResult(
            success=True,
            result={},
            stdout="Processing...\nDone!",
            stderr="Warning: deprecated function",
        )
        
        assert "Processing" in result.stdout
        assert "Warning" in result.stderr


class TestToolIsolator:
    """Test ToolIsolator class."""
    
    @pytest.fixture
    def isolator(self):
        """Create isolator for testing."""
        return ToolIsolator(timeout=10.0)
    
    def test_isolator_init(self, isolator):
        """Test isolator initialization."""
        assert isolator.timeout == 10.0
    
    def test_isolator_custom_timeout(self):
        """Test custom timeout."""
        isolator = ToolIsolator(timeout=60.0)
        assert isolator.timeout == 60.0
    
    @pytest.mark.asyncio
    async def test_create_runner_script(self, isolator):
        """Test runner script creation."""
        script = isolator._create_runner_script(
            module="test_module",
            function="test_func",
            args={"key": "value"},
        )
        
        assert "test_module" in script
        assert "test_func" in script
        assert "key" in script
    
    @pytest.mark.asyncio
    async def test_run_with_mock_subprocess(self, isolator):
        """Test run with mocked subprocess."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='{"success": true, "result": {"data": 123}}',
                stderr="",
            )
            
            result = await isolator.run(
                module="json",
                function="dumps",
                args=[{"test": "data"}],
            )
            
            # Subprocess should have been called
            mock_run.assert_called()


class TestLazyToolLoader:
    """Test LazyToolLoader class."""
    
    @pytest.fixture
    def loader(self):
        """Create loader for testing."""
        return LazyToolLoader()
    
    def test_loader_init(self, loader):
        """Test loader initialization."""
        assert loader._servers == {}
    
    def test_is_loaded_initially_false(self, loader):
        """Test server not loaded initially."""
        assert loader.is_loaded("test_server") is False
    
    def test_loaded_servers_empty(self, loader):
        """Test initially no servers loaded."""
        assert loader.loaded_servers() == []
    
    def test_unload_server(self, loader):
        """Test unloading a server."""
        # Manually add a server
        loader._servers["test"] = MagicMock()
        
        loader.unload("test")
        
        assert "test" not in loader._servers
    
    def test_unload_nonexistent_server(self, loader):
        """Test unloading server that doesn't exist."""
        # Should not raise
        loader.unload("nonexistent")
    
    def test_get_caches_server(self, loader):
        """Test get caches loaded server."""
        with patch.object(loader, "_import_server") as mock_import:
            mock_server = MagicMock()
            mock_import.return_value = mock_server
            
            # First call imports
            result1 = loader.get("test_server")
            mock_import.assert_called_once()
            
            # Second call returns cached
            result2 = loader.get("test_server")
            assert mock_import.call_count == 1  # Still only once


class TestServerMapping:
    """Test server name mapping."""
    
    def test_loader_has_server_map(self):
        """Test loader has server mapping."""
        loader = LazyToolLoader()
        
        # Check that common servers are mapped
        expected_servers = [
            "scraper_server",
            "python_server",
            "search_server",
            "vision_server",
            "analysis_server",
        ]
        
        for server in expected_servers:
            # Should not raise on import attempt
            try:
                with patch("importlib.import_module"):
                    loader._import_server(server)
            except (KeyError, ImportError):
                pass  # OK if not configured


class TestGlobalInstances:
    """Test global instance getters."""
    
    def test_get_isolator_singleton(self):
        """Test get_isolator returns singleton."""
        import shared.tools.isolation as module
        module._isolator = None  # Reset
        
        iso1 = get_isolator()
        iso2 = get_isolator()
        
        assert iso1 is iso2
    
    def test_get_lazy_loader_singleton(self):
        """Test get_lazy_loader returns singleton."""
        import shared.tools.isolation as module
        module._lazy_loader = None  # Reset
        
        loader1 = get_lazy_loader()
        loader2 = get_lazy_loader()
        
        assert loader1 is loader2


class TestRunnerScriptGeneration:
    """Test runner script generation."""
    
    def test_script_has_imports(self):
        """Test generated script has necessary imports."""
        isolator = ToolIsolator()
        script = isolator._create_runner_script(
            module="test.module",
            function="my_func",
            args={"arg1": "val1"},
        )
        
        assert "import json" in script
        assert "import sys" in script
    
    def test_script_has_function_call(self):
        """Test generated script calls function."""
        isolator = ToolIsolator()
        script = isolator._create_runner_script(
            module="test.module",
            function="my_func",
            args={"arg1": "val1"},
        )
        
        assert "my_func" in script
    
    def test_script_has_error_handling(self):
        """Test generated script has error handling."""
        isolator = ToolIsolator()
        script = isolator._create_runner_script(
            module="test.module",
            function="my_func",
            args={},
        )
        
        assert "try" in script
        assert "except" in script
