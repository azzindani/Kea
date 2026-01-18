"""
Scraper MCP Server.

Provides web scraping tools via MCP protocol.
"""

from __future__ import annotations

import asyncio

from shared.mcp.server_base import MCPServer
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger

from mcp_servers.scraper_server.tools.fetch_url import fetch_url_tool
from mcp_servers.scraper_server.tools.browser_scrape import browser_scrape_tool


logger = get_logger(__name__)


class ScraperServer(MCPServer):
    """
    MCP Server for web scraping.
    
    Tools:
    - fetch_url: Fetch URL via HTTP GET
    - browser_scrape: Scrape with headless browser
    """
    
    def __init__(self) -> None:
        super().__init__(name="scraper_server", version="1.0.0")
        self._register_tools()
    
    def _register_tools(self) -> None:
        """Register all scraper tools."""
        
        # fetch_url tool
        self.register_tool(
            name="fetch_url",
            description="Fetch URL content via HTTP GET request. Returns HTML/text content.",
            handler=self._handle_fetch_url,
            parameters={
                "url": {
                    "type": "string",
                    "description": "URL to fetch"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Request timeout in seconds (default: 30)"
                },
                "headers": {
                    "type": "object",
                    "description": "Optional HTTP headers"
                }
            },
            required=["url"]
        )
        
        # browser_scrape tool
        self.register_tool(
            name="browser_scrape",
            description="Scrape URL using headless browser with JavaScript execution. Use for dynamic content.",
            handler=self._handle_browser_scrape,
            parameters={
                "url": {
                    "type": "string",
                    "description": "URL to scrape"
                },
                "wait_for": {
                    "type": "string",
                    "description": "CSS selector to wait for before scraping"
                },
                "extract_tables": {
                    "type": "boolean",
                    "description": "Extract tables as structured data (default: true)"
                },
                "screenshot": {
                    "type": "boolean",
                    "description": "Take screenshot (default: false)"
                }
            },
            required=["url"]
        )
    
    async def _handle_fetch_url(self, arguments: dict) -> ToolResult:
        """Handle fetch_url tool call."""
        logger.info("Executing fetch_url", extra={"url": arguments.get("url")})
        return await fetch_url_tool(arguments)
    
    async def _handle_browser_scrape(self, arguments: dict) -> ToolResult:
        """Handle browser_scrape tool call."""
        logger.info("Executing browser_scrape", extra={"url": arguments.get("url")})
        return await browser_scrape_tool(arguments)


async def main() -> None:
    """Run the scraper server."""
    from shared.logging import setup_logging, LogConfig
    
    setup_logging(LogConfig(level="DEBUG", format="console", service_name="scraper_server"))
    
    # JIT Browser Installation
    # Ensure browsers are installed since we are running in an isolated uv environment
    import subprocess
    logger.info("🔧 Verifying Playwright browsers (JIT)...")
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception as e:
        logger.warning(f"Failed to auto-install browsers: {e}")

    server = ScraperServer()
    logger.info(f"Starting {server.name} with {len(server.get_tools())} tools")
    
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
