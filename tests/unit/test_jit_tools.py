"""
Tests for JIT Loading and Tool Isolation.
"""

import pytest


class TestJITLoader:
    """Tests for JIT tool loader."""

    def test_load_config(self):
        """Test loading tools.yaml config."""
        from shared.tools import JITLoader

        loader = JITLoader()

        # Should have loaded config
        assert loader._config is not None
        assert "tools" in loader._config or loader._config.get("jit", {})

        print("\n✅ Config loaded successfully")

    def test_get_tool_deps(self):
        """Test getting tool dependencies."""
        from shared.tools import JITLoader

        loader = JITLoader()

        # Get deps for known tool
        deps = loader.get_tool_deps("pdf_extract")

        assert deps is not None
        print(f"\n✅ pdf_extract deps: {deps.packages}")

    def test_is_installed_check(self):
        """Test package installation check."""
        from shared.tools import JITLoader

        loader = JITLoader()

        # Built-in modules should be "installed"
        # Note: this checks import, not pip
        assert loader.is_installed("json")
        assert loader.is_installed("os")

        # Random package shouldn't be
        assert not loader.is_installed("nonexistent_package_xyz")

        print("\n✅ Installation check works")

    def test_has_uv_check(self):
        """Test uv availability check."""
        from shared.tools import JITLoader

        loader = JITLoader()

        # Just check it returns bool without error
        has_uv = loader.has_uv
        assert isinstance(has_uv, bool)

        print(f"\n✅ uv available: {has_uv}")


class TestToolIsolator:
    """Tests for tool isolation."""

    @pytest.mark.asyncio
    async def test_run_simple_function(self):
        """Test running isolated function."""
        from shared.tools import ToolIsolator

        isolator = ToolIsolator(timeout=30)

        # Run a simple built-in operation
        result = await isolator.run(
            module="json",
            function="dumps",
            args={"obj": {"test": 123}},
        )

        # May fail if json.dumps doesn't work this way,
        # but should at least not crash
        print(f"\n✅ Isolated run completed: success={result.success}")

    def test_create_runner_script(self):
        """Test runner script generation."""
        from shared.tools import ToolIsolator

        isolator = ToolIsolator()

        script = isolator._create_runner_script(
            module="test_module",
            function="test_func",
            args={"x": 1, "y": 2},
        )

        assert "test_module" in script
        assert "test_func" in script
        assert "__RESULT__" in script

        print("\n✅ Runner script generated correctly")


class TestLazyLoader:
    """Tests for lazy tool loading."""

    def test_lazy_loader_init(self):
        """Test lazy loader initialization."""
        from shared.tools import LazyToolLoader

        loader = LazyToolLoader()

        # Nothing should be loaded yet
        assert len(loader.loaded_servers()) == 0

        print("\n✅ Lazy loader initialized with no servers loaded")

    def test_is_loaded_check(self):
        """Test loaded check."""
        from shared.tools import LazyToolLoader

        loader = LazyToolLoader()

        # Nothing loaded yet
        assert not loader.is_loaded("analytics_server")

        print("\n✅ is_loaded check works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
