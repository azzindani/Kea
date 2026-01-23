"""
Parallel Tool Executor.

Execute multiple MCP tool calls concurrently with rate limiting.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Callable, Awaitable

from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger
from shared.logging.metrics import record_tool_call, ACTIVE_TOOLS


logger = get_logger(__name__)


@dataclass
class ToolCall:
    """A tool call request."""
    tool_name: str
    arguments: dict[str, Any]
    priority: int = 0  # Higher = more priority


@dataclass
class ToolCallResult:
    """Result of a tool call."""
    tool_name: str
    arguments: dict[str, Any]
    result: ToolResult
    duration_ms: float
    success: bool


class ParallelExecutor:
    """
    Execute multiple tool calls in parallel with concurrency control.
    
    Features:
    - Configurable max concurrency
    - Rate limiting per server
    - Priority queue
    - Timeout handling
    - Metrics tracking
    
    Example:
        executor = ParallelExecutor(max_concurrent=5)
        
        calls = [
            ToolCall("fetch_url", {"url": "https://example1.com"}),
            ToolCall("fetch_url", {"url": "https://example2.com"}),
            ToolCall("web_search", {"query": "test"}),
        ]
        
        results = await executor.execute_batch(calls, tool_handler)
    """
    
    def __init__(
        self,
        max_concurrent: int | None = None,
        timeout_seconds: float = 60.0,
        rate_limit_per_second: float = 10.0,
    ) -> None:
        # Hardware-aware auto-detection if not specified
        if max_concurrent is None:
            from shared.hardware.detector import detect_hardware
            hw = detect_hardware()
            max_concurrent = hw.optimal_workers()
            logger.info(f"ParallelExecutor: auto-detected {max_concurrent} workers")
        
        self.max_concurrent = max_concurrent
        self.timeout_seconds = timeout_seconds
        self.rate_limit_per_second = rate_limit_per_second
        
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._last_call_time: dict[str, float] = {}  # server_name -> timestamp
        self._min_interval = 1.0 / rate_limit_per_second if rate_limit_per_second > 0 else 0
    
    async def execute_batch(
        self,
        calls: list[ToolCall],
        handler: Callable[[str, dict[str, Any]], Awaitable[ToolResult]],
        server_for_tool: Callable[[str], str | None] | None = None,
    ) -> list[ToolCallResult]:
        """
        Execute a batch of tool calls in parallel.
        
        Args:
            calls: List of tool calls to execute
            handler: Async function to execute each tool
            server_for_tool: Optional function to get server name for rate limiting
            
        Returns:
            List of results in same order as calls
        """
        # Sort by priority (higher first)
        indexed_calls = list(enumerate(calls))
        indexed_calls.sort(key=lambda x: x[1].priority, reverse=True)
        
        # Execute with concurrency control
        tasks = []
        for original_idx, call in indexed_calls:
            server_name = None
            if server_for_tool:
                server_name = server_for_tool(call.tool_name)
            
            task = asyncio.create_task(
                self._execute_single(call, handler, server_name, original_idx)
            )
            tasks.append(task)
        
        # Wait for all to complete
        results_with_idx = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Sort back to original order
        results = [None] * len(calls)
        for result in results_with_idx:
            if isinstance(result, Exception):
                logger.error(f"Tool execution error: {result}")
                continue
            if result is not None:
                idx, tool_result = result
                results[idx] = tool_result
        
        # Fill in None results with errors
        for i, r in enumerate(results):
            if r is None:
                results[i] = ToolCallResult(
                    tool_name=calls[i].tool_name,
                    arguments=calls[i].arguments,
                    result=ToolResult(
                        content=[TextContent(text="Execution failed")],
                        isError=True
                    ),
                    duration_ms=0,
                    success=False,
                )
        
        return results
    
    async def _execute_single(
        self,
        call: ToolCall,
        handler: Callable[[str, dict[str, Any]], Awaitable[ToolResult]],
        server_name: str | None,
        original_idx: int,
    ) -> tuple[int, ToolCallResult]:
        """Execute a single tool call with rate limiting."""
        async with self._semaphore:
            # Rate limiting
            if server_name and self._min_interval > 0:
                await self._wait_for_rate_limit(server_name)
            
            start_time = time.perf_counter()
            
            try:
                if server_name:
                    ACTIVE_TOOLS.labels(server_name=server_name).inc()
                
                # Execute with timeout
                result = await asyncio.wait_for(
                    handler(call.tool_name, call.arguments),
                    timeout=self.timeout_seconds
                )
                
                duration_ms = (time.perf_counter() - start_time) * 1000
                success = not result.isError
                
                # Record metrics
                if server_name:
                    record_tool_call(call.tool_name, server_name, duration_ms / 1000, success)
                
                return original_idx, ToolCallResult(
                    tool_name=call.tool_name,
                    arguments=call.arguments,
                    result=result,
                    duration_ms=duration_ms,
                    success=success,
                )
                
            except asyncio.TimeoutError:
                duration_ms = (time.perf_counter() - start_time) * 1000
                
                return original_idx, ToolCallResult(
                    tool_name=call.tool_name,
                    arguments=call.arguments,
                    result=ToolResult(
                        content=[TextContent(text=f"Timeout after {self.timeout_seconds}s")],
                        isError=True
                    ),
                    duration_ms=duration_ms,
                    success=False,
                )
                
            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.error(f"Tool {call.tool_name} error: {e}")
                
                return original_idx, ToolCallResult(
                    tool_name=call.tool_name,
                    arguments=call.arguments,
                    result=ToolResult(
                        content=[TextContent(text=f"Error: {str(e)}")],
                        isError=True
                    ),
                    duration_ms=duration_ms,
                    success=False,
                )
                
            finally:
                if server_name:
                    ACTIVE_TOOLS.labels(server_name=server_name).dec()
    
    async def _wait_for_rate_limit(self, server_name: str) -> None:
        """Wait if needed for rate limiting."""
        last_time = self._last_call_time.get(server_name, 0)
        elapsed = time.time() - last_time
        
        if elapsed < self._min_interval:
            await asyncio.sleep(self._min_interval - elapsed)
        
        self._last_call_time[server_name] = time.time()


async def execute_tools_parallel(
    calls: list[tuple[str, dict[str, Any]]],
    handler: Callable[[str, dict[str, Any]], Awaitable[ToolResult]],
    max_concurrent: int = 5,
) -> list[ToolResult]:
    """
    Convenience function to execute tools in parallel.
    
    Args:
        calls: List of (tool_name, arguments) tuples
        handler: Async handler function
        max_concurrent: Max concurrent executions
        
    Returns:
        List of ToolResults in same order
    """
    executor = ParallelExecutor(max_concurrent=max_concurrent)
    
    tool_calls = [ToolCall(name, args) for name, args in calls]
    results = await executor.execute_batch(tool_calls, handler)
    
    return [r.result for r in results]
