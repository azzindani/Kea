"""
Batch Scrape Tool.

Scrape multiple URLs in parallel.
"""

from __future__ import annotations

import asyncio
from typing import Any

from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger

from mcp_servers.scraper_server.tools.fetch_url import fetch_url_tool


logger = get_logger(__name__)


async def batch_scrape_tool(arguments: dict) -> ToolResult:
    """
    Scrape multiple URLs in parallel.
    
    Args:
        arguments: Tool arguments containing:
            - urls: List of URLs to scrape
            - max_concurrent: Max parallel requests (default: 5)
            - timeout: Per-URL timeout (default: 30)
    
    Returns:
        ToolResult with combined results
    """
    urls = arguments.get("urls", [])
    max_concurrent = arguments.get("max_concurrent", 5)
    timeout = arguments.get("timeout", 30)
    
    if not urls:
        return ToolResult(
            content=[TextContent(text="Error: urls list is required")],
            isError=True
        )
    
    if not isinstance(urls, list):
        return ToolResult(
            content=[TextContent(text="Error: urls must be a list")],
            isError=True
        )
    
    logger.info(f"Batch scraping {len(urls)} URLs with max_concurrent={max_concurrent}")
    
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def scrape_one(url: str) -> dict:
        async with semaphore:
            try:
                result = await fetch_url_tool({"url": url, "timeout": timeout})
                return {
                    "url": url,
                    "success": not result.isError,
                    "content": result.content[0].text[:5000] if result.content else "",
                }
            except Exception as e:
                return {
                    "url": url,
                    "success": False,
                    "content": f"Error: {str(e)}",
                }
    
    # Execute all in parallel
    tasks = [scrape_one(url) for url in urls]
    results = await asyncio.gather(*tasks)
    
    # Build output
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    
    output = f"## Batch Scrape Results\n\n"
    output += f"**Total URLs:** {len(urls)}\n"
    output += f"**Successful:** {successful}\n"
    output += f"**Failed:** {failed}\n\n"
    
    output += "---\n\n"
    
    for i, result in enumerate(results, 1):
        status = "✅" if result["success"] else "❌"
        output += f"### {i}. {status} {result['url']}\n\n"
        
        if result["success"]:
            # Truncate content preview
            preview = result["content"][:500]
            output += f"```\n{preview}\n```\n\n"
        else:
            output += f"*{result['content']}*\n\n"
    
    return ToolResult(content=[TextContent(text=output)])
