"""
Unit Tests: Parallel Executor.

Tests for services/orchestrator/mcp/parallel_executor.py.
"""

import pytest
import asyncio


class TestParallelExecutor:
    """Tests for parallel tool executor."""
    
    @pytest.mark.asyncio
    async def test_execute_single(self):
        """Execute single tool call."""
        from services.orchestrator.mcp.parallel_executor import ParallelExecutor, ToolCall
        from shared.mcp.protocol import ToolResult, TextContent
        
        async def mock_handler(name, args):
            return ToolResult(content=[TextContent(text=f"Result for {name}")])
        
        executor = ParallelExecutor(max_concurrent=5)
        
        calls = [ToolCall("test_tool", {"arg": "value"})]
        results = await executor.execute_batch(calls, mock_handler)
        
        assert len(results) == 1
        assert results[0].success
        assert "test_tool" in results[0].result.content[0].text
    
    @pytest.mark.asyncio
    async def test_execute_parallel(self):
        """Execute multiple calls in parallel."""
        from services.orchestrator.mcp.parallel_executor import ParallelExecutor, ToolCall
        from shared.mcp.protocol import ToolResult, TextContent
        
        call_times = []
        
        async def mock_handler(name, args):
            call_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.1)
            return ToolResult(content=[TextContent(text=f"OK")])
        
        executor = ParallelExecutor(max_concurrent=5)
        
        calls = [ToolCall(f"tool_{i}", {}) for i in range(3)]
        results = await executor.execute_batch(calls, mock_handler)
        
        assert len(results) == 3
        assert all(r.success for r in results)
    
    @pytest.mark.asyncio
    async def test_handle_error(self):
        """Handle tool execution error."""
        from services.orchestrator.mcp.parallel_executor import ParallelExecutor, ToolCall
        from shared.mcp.protocol import ToolResult, TextContent
        
        async def error_handler(name, args):
            raise ValueError("Test error")
        
        executor = ParallelExecutor(max_concurrent=5)
        
        calls = [ToolCall("error_tool", {})]
        results = await executor.execute_batch(calls, error_handler)
        
        assert len(results) == 1
        assert not results[0].success
        assert results[0].result.isError
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Handle tool execution timeout."""
        from services.orchestrator.mcp.parallel_executor import ParallelExecutor, ToolCall
        from shared.mcp.protocol import ToolResult, TextContent
        
        async def slow_handler(name, args):
            await asyncio.sleep(10)  # Very slow
            return ToolResult(content=[TextContent(text="Done")])
        
        executor = ParallelExecutor(max_concurrent=5, timeout_seconds=0.5)
        
        calls = [ToolCall("slow_tool", {})]
        results = await executor.execute_batch(calls, slow_handler)
        
        assert len(results) == 1
        assert not results[0].success
        assert "Timeout" in results[0].result.content[0].text


class TestExecuteToolsParallel:
    """Tests for convenience function."""
    
    @pytest.mark.asyncio
    async def test_execute_tools_parallel(self):
        """Test convenience function."""
        from services.orchestrator.mcp.parallel_executor import execute_tools_parallel
        from shared.mcp.protocol import ToolResult, TextContent
        
        async def handler(name, args):
            return ToolResult(content=[TextContent(text=f"{name}:{args}")])
        
        calls = [
            ("tool1", {"a": 1}),
            ("tool2", {"b": 2}),
        ]
        
        results = await execute_tools_parallel(calls, handler, max_concurrent=3)
        
        assert len(results) == 2
        assert all(not r.isError for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
