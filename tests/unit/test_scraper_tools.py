"""
Unit Tests: Scraper Tools.

Tests for mcp_servers/scraper_server/tools/*.py
"""

import pytest


class TestFetchUrlTool:
    """Tests for fetch_url tool."""
    
    @pytest.mark.asyncio
    async def test_fetch_example_domain(self):
        """Fetch example.com."""
        from mcp_servers.scraper_server.tools.fetch_url import fetch_url_tool
        
        result = await fetch_url_tool({"url": "https://example.com"})
        
        assert result is not None
        assert not result.isError
        assert "Example Domain" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_fetch_with_timeout(self):
        """Fetch with custom timeout."""
        from mcp_servers.scraper_server.tools.fetch_url import fetch_url_tool
        
        result = await fetch_url_tool({
            "url": "https://example.com",
            "timeout": 15,
        })
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_fetch_invalid_url(self):
        """Handle invalid URL."""
        from mcp_servers.scraper_server.tools.fetch_url import fetch_url_tool
        
        result = await fetch_url_tool({"url": "not-a-valid-url"})
        
        assert result.isError


class TestBatchScrapeTool:
    """Tests for batch_scrape tool."""
    
    @pytest.mark.asyncio
    async def test_batch_single_url(self):
        """Batch scrape single URL."""
        from mcp_servers.scraper_server.tools.batch_scrape import batch_scrape_tool
        
        result = await batch_scrape_tool({
            "urls": ["https://example.com"],
            "max_concurrent": 1,
        })
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_batch_multiple_urls(self):
        """Batch scrape multiple URLs."""
        from mcp_servers.scraper_server.tools.batch_scrape import batch_scrape_tool
        
        result = await batch_scrape_tool({
            "urls": ["https://example.com", "https://example.org"],
            "max_concurrent": 2,
        })
        
        assert result is not None


class TestBrowserScrapeTool:
    """Tests for browser_scrape tool."""
    
    @pytest.mark.asyncio
    async def test_browser_scrape_basic(self):
        """Browser scrape basic page."""
        try:
            from mcp_servers.scraper_server.tools.browser_scrape import browser_scrape_tool
            
            result = await browser_scrape_tool({
                "url": "https://example.com",
                "wait_for": "body",
            })
            
            # May fail if playwright not installed
            assert result is not None
        except ImportError:
            pytest.skip("Playwright not installed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
