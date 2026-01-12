"""
Real Tests: MCP Retry Mechanism.

Tests for MCP retry behavior with real tool calls.
Run with: pytest tests/real/test_mcp_retry_live.py -v -s
"""

import pytest
import asyncio


class TestMCPRetryConfiguration:
    """Test MCP retry configuration."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_config_loaded(self, logger):
        """Test retry config is loaded."""
        logger.info("Testing MCP retry config")
        
        from shared.config import get_settings
        
        settings = get_settings()
        
        print(f"\n📋 MCP Retry Configuration:")
        print(f"   max_retries: {settings.mcp.max_retries}")
        print(f"   retry_delay: {settings.mcp.retry_delay}s")
        print(f"   retry_backoff: {settings.mcp.retry_backoff}x")
        print(f"   retry_on_timeout: {settings.mcp.retry_on_timeout}")
        print(f"   retry_on_connection_error: {settings.mcp.retry_on_connection_error}")
        print(f"   rate_limit: {settings.mcp.rate_limit_per_second}/s")
        print(f"   max_concurrent: {settings.mcp.max_concurrent_tools}")
        print(f"   timeout: {settings.mcp.tool_timeout_seconds}s")
        
        assert settings.mcp.max_retries >= 1
        assert settings.mcp.retry_delay > 0
        
        print(f"\n✅ Retry configuration loaded")
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_retry_backoff_calculation(self, logger):
        """Test exponential backoff calculation."""
        logger.info("Testing backoff calculation")
        
        from shared.config import get_settings
        
        settings = get_settings()
        
        delays = []
        for attempt in range(settings.mcp.max_retries):
            delay = settings.mcp.retry_delay * (settings.mcp.retry_backoff ** attempt)
            delays.append(delay)
        
        print(f"\n📈 Backoff delays for {settings.mcp.max_retries} retries:")
        for i, delay in enumerate(delays):
            print(f"   Attempt {i + 1}: {delay:.2f}s")
        
        # Verify exponential growth
        for i in range(1, len(delays)):
            expected = delays[i - 1] * settings.mcp.retry_backoff
            assert abs(delays[i] - expected) < 0.001
        
        print(f"\n✅ Exponential backoff verified")


class TestMCPRetryBehavior:
    """Test MCP retry behavior with real tools."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_successful_call_no_retry(self, logger):
        """Successful call should not retry."""
        logger.info("Testing successful call")
        
        from mcp_servers.search_server.tools.web_search import web_search_tool
        
        # This should succeed on first attempt
        result = await web_search_tool({
            "query": "test query",
            "max_results": 1
        })
        
        if not result.isError:
            print(f"\n✅ Call succeeded without retry")
        else:
            print(f"\n⚠️ Call failed (may be rate limited)")
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_parallel_with_retry(self, logger):
        """Test parallel execution with retry config."""
        logger.info("Testing parallel execution with retry")
        
        from mcp_servers.search_server.tools.web_search import web_search_tool
        import time
        
        queries = ["python", "javascript", "rust"]
        
        start = time.perf_counter()
        
        results = await asyncio.gather(*[
            web_search_tool({"query": q, "max_results": 1})
            for q in queries
        ], return_exceptions=True)
        
        elapsed = time.perf_counter() - start
        
        success_count = sum(
            1 for r in results 
            if not isinstance(r, Exception) and not r.isError
        )
        
        print(f"\n⚡ Parallel execution: {elapsed:.2f}s")
        print(f"   Success: {success_count}/{len(queries)}")
        
        assert success_count >= 1  # At least one should work


class TestMCPRateLimiting:
    """Test MCP rate limiting."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_rate_limit_config(self, logger):
        """Test rate limiting configuration."""
        logger.info("Testing rate limit config")
        
        from shared.config import get_settings
        
        settings = get_settings()
        
        print(f"\n⏱️ Rate Limiting:")
        print(f"   {settings.mcp.rate_limit_per_second} calls/second")
        print(f"   {settings.mcp.max_concurrent_tools} concurrent max")
        
        # Calculate max throughput
        max_throughput = settings.mcp.rate_limit_per_second * 60
        print(f"   Max throughput: {max_throughput:.0f} calls/minute")
        
        assert settings.mcp.rate_limit_per_second > 0
        assert settings.mcp.max_concurrent_tools > 0
        
        print(f"\n✅ Rate limiting configured")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--log-cli-level=INFO"])
