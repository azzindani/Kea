"""
MCP Parallel Execution Live Tests.

Tests parallel tool execution across multiple MCP servers.
Run with: pytest tests/real/test_mcp_parallel_live.py -v -s --log-cli-level=INFO
"""

import pytest
import asyncio
import time
from shared.llm.provider import LLMMessage, LLMRole, LLMConfig

from tests.real.conftest import print_stream


class TestMCPParallelExecution:
    """Test parallel execution of MCP tools."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_parallel_search(self, logger):
        """Execute multiple searches in parallel."""
        logger.info("Testing parallel search execution")
        
        from mcp_servers.search_server.tools.web_search import web_search_tool
        from mcp_servers.search_server.tools.academic_search import academic_search_tool
        
        start = time.perf_counter()
        
        # Run searches in parallel
        results = await asyncio.gather(
            web_search_tool({"query": "python programming", "max_results": 3}),
            web_search_tool({"query": "machine learning", "max_results": 3}),
            academic_search_tool({"query": "deep learning", "source": "arxiv", "max_results": 2}),
            return_exceptions=True
        )
        
        elapsed = time.perf_counter() - start
        
        print(f"\n⚡ Parallel Execution: {elapsed:.2f}s for 3 searches")
        
        success_count = sum(1 for r in results if not isinstance(r, Exception) and not r.isError)
        print(f"✅ Successful: {success_count}/3")
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"   Search {i+1}: Error - {result}")
            else:
                print(f"   Search {i+1}: {len(result.content[0].text)} chars")
        
        assert success_count >= 2, "At least 2 searches should succeed"
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_parallel_multi_server(self, logger):
        """Execute tools from different servers in parallel."""
        logger.info("Testing multi-server parallel execution")
        
        from mcp_servers.search_server.tools.web_search import web_search_tool
        from mcp_servers.scraper_server.tools.fetch_url import fetch_url_tool
        from mcp_servers.analysis_server.server import AnalysisServer
        
        analysis = AnalysisServer()
        
        start = time.perf_counter()
        
        # Run different server tools in parallel
        results = await asyncio.gather(
            web_search_tool({"query": "renewable energy", "max_results": 3}),
            fetch_url_tool({"url": "https://example.com"}),
            analysis._handle_trend_detection({
                "data": [10, 15, 20, 25, 30],
                "metric_name": "test"
            }),
            return_exceptions=True
        )
        
        elapsed = time.perf_counter() - start
        
        print(f"\n⚡ Multi-Server Parallel: {elapsed:.2f}s")
        
        success_count = 0
        for i, (name, result) in enumerate(zip(["Search", "Scraper", "Analysis"], results)):
            if isinstance(result, Exception):
                print(f"   {name}: Error - {result}")
            elif result.isError:
                print(f"   {name}: Tool error")
            else:
                print(f"   {name}: ✅ {len(result.content[0].text)} chars")
                success_count += 1
        
        assert success_count >= 2, "At least 2 servers should succeed"
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_parallel_with_llm_analysis(self, llm_provider, llm_config, logger):
        """Parallel data gathering + sequential LLM analysis."""
        logger.info("Testing parallel gather + LLM analysis")
        
        from mcp_servers.search_server.tools.web_search import web_search_tool
        from mcp_servers.search_server.tools.academic_search import academic_search_tool
        
        # Parallel data gathering
        start = time.perf_counter()
        
        results = await asyncio.gather(
            web_search_tool({"query": "AI ethics", "max_results": 3}),
            academic_search_tool({"query": "artificial intelligence ethics", "source": "arxiv", "max_results": 2}),
        )
        
        gather_time = time.perf_counter() - start
        print(f"\n⚡ Gather Phase: {gather_time:.2f}s")
        
        # Combine results
        combined_text = ""
        for r in results:
            if not r.isError:
                combined_text += r.content[0].text[:500] + "\n\n"
        
        print(f"📚 Combined: {len(combined_text)} chars")
        
        # LLM analysis
        start = time.perf_counter()
        
        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content="You are a research analyst. Be concise."),
            LLMMessage(role=LLMRole.USER, content=f"Summarize key themes from:\n\n{combined_text[:1500]}")
        ]
        
        content, _ = await print_stream(llm_provider, messages, llm_config, "LLM Analysis")
        
        llm_time = time.perf_counter() - start
        
        print(f"⚡ Analysis Phase: {llm_time:.2f}s")
        print(f"⚡ Total Pipeline: {gather_time + llm_time:.2f}s")
        
        assert len(content) > 50


class TestParallelExecutorIntegration:
    """Test the parallel executor component."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_parallel_executor_batch(self, logger):
        """Test parallel executor with batch of tasks."""
        from services.orchestrator.mcp.parallel_executor import execute_tools_parallel, ToolCall
        from mcp_servers.search_server.tools.web_search import web_search_tool
        
        logger.info("Testing parallel executor")
        
        # Define a simple handler
        async def tool_handler(tool_name: str, args: dict):
            if tool_name == "web_search":
                return await web_search_tool(args)
            return None
        
        calls = [
            ("web_search", {"query": "Python", "max_results": 2}),
            ("web_search", {"query": "JavaScript", "max_results": 2}),
        ]
        
        results = await execute_tools_parallel(calls, tool_handler, max_concurrent=2)
        
        print(f"\n⚡ Parallel Results: {len(results)} completed")
        for i, result in enumerate(results):
            if result and result.content:
                print(f"   {i+1}. {len(result.content[0].text)} chars")
        
        assert len(results) == 2
        assert all(r is not None for r in results)


class TestConcurrentLLMCalls:
    """Test concurrent LLM API calls."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_concurrent_completions(self, llm_provider, llm_config, logger):
        """Test multiple LLM calls concurrently."""
        logger.info("Testing concurrent LLM completions")
        
        prompts = [
            "What is 2+2?",
            "Name a color.",
            "Say hello.",
        ]
        
        async def get_completion(prompt):
            messages = [LLMMessage(role=LLMRole.USER, content=prompt)]
            return await llm_provider.complete(messages, llm_config)
        
        start = time.perf_counter()
        
        results = await asyncio.gather(*[get_completion(p) for p in prompts])
        
        elapsed = time.perf_counter() - start
        
        print(f"\n⚡ Concurrent LLM: {elapsed:.2f}s for {len(prompts)} completions")
        
        for i, result in enumerate(results):
            print(f"   Q: {prompts[i]} → A: {result.content[:50]}...")
        
        assert len(results) == len(prompts)
        assert all(r.content for r in results)


class TestBatchProcessing:
    """Test batch processing patterns."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_batch_scrape_parallel(self, logger):
        """Test batch URL scraping."""
        from mcp_servers.scraper_server.tools.batch_scrape import batch_scrape_tool
        
        logger.info("Testing batch scraping")
        
        result = await batch_scrape_tool({
            "urls": [
                "https://example.com",
                "https://httpbin.org/html"
            ],
            "max_concurrent": 2
        })
        
        content = result.content[0].text
        print(f"\n📦 Batch Results:\n{content[:500]}")
        
        assert "Batch Scrape Results" in content
        assert not result.isError


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--log-cli-level=INFO"])
