# Scraper MCP Server Package
"""
Web scraping MCP server with Playwright and stealth capabilities.

Tools:
- fetch_url: Simple HTTP GET
- browser_scrape: Headless browser scraping
- batch_scrape: Parallel URL processing
"""

from mcp_servers.scraper_server.server import ScraperServer

__all__ = ["ScraperServer"]
