"""
Web Search Tool.

Multi-provider web search (Tavily, Brave, DuckDuckGo fallback).
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger


logger = get_logger(__name__)


async def web_search_tool(arguments: dict) -> ToolResult:
    """
    Execute web search.
    
    Args:
        arguments: Tool arguments containing:
            - query: Search query
            - max_results: Max results (default 10)
            - search_depth: basic or advanced
    
    Returns:
        ToolResult with search results
    """
    query = arguments.get("query", "")
    max_results = arguments.get("max_results", 10)
    search_depth = arguments.get("search_depth", "basic")
    
    if not query:
        return ToolResult(
            content=[TextContent(text="Error: Query is required")],
            isError=True
        )
    
    # Try Tavily first
    tavily_key = os.getenv("TAVILY_API_KEY", "")
    if tavily_key:
        return await _tavily_search(query, max_results, search_depth, tavily_key)
    
    # Try Brave Search
    brave_key = os.getenv("BRAVE_API_KEY", "")
    if brave_key:
        return await _brave_search(query, max_results, brave_key)
    
    # Fallback to DuckDuckGo (no API key needed)
    return await _duckduckgo_search(query, max_results)


async def _tavily_search(query: str, max_results: int, search_depth: str, api_key: str) -> ToolResult:
    """Search using Tavily API."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": search_depth,
                    "include_answer": True,
                }
            )
            response.raise_for_status()
            data = response.json()
        
        output = f"## Web Search Results\n\n**Query:** {query}\n\n"
        
        # Include AI answer if available
        if data.get("answer"):
            output += f"### Quick Answer\n{data['answer']}\n\n"
        
        output += "### Results\n\n"
        
        for i, result in enumerate(data.get("results", []), 1):
            output += f"**{i}. [{result.get('title', 'No title')}]({result.get('url', '')})**\n"
            output += f"{result.get('content', '')[:300]}...\n\n"
        
        return ToolResult(content=[TextContent(text=output)])
        
    except Exception as e:
        logger.error(f"Tavily search error: {e}")
        return ToolResult(
            content=[TextContent(text=f"Search Error: {str(e)}")],
            isError=True
        )


async def _brave_search(query: str, max_results: int, api_key: str) -> ToolResult:
    """Search using Brave Search API."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": max_results},
                headers={"X-Subscription-Token": api_key}
            )
            response.raise_for_status()
            data = response.json()
        
        output = f"## Web Search Results (Brave)\n\n**Query:** {query}\n\n"
        
        for i, result in enumerate(data.get("web", {}).get("results", []), 1):
            output += f"**{i}. [{result.get('title', 'No title')}]({result.get('url', '')})**\n"
            output += f"{result.get('description', '')[:300]}...\n\n"
        
        return ToolResult(content=[TextContent(text=output)])
        
    except Exception as e:
        logger.error(f"Brave search error: {e}")
        return ToolResult(
            content=[TextContent(text=f"Search Error: {str(e)}")],
            isError=True
        )


async def _duckduckgo_search(query: str, max_results: int) -> ToolResult:
    """Fallback search using DuckDuckGo HTML scraping."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
            response.raise_for_status()
        
        # Parse results (basic extraction)
        from html.parser import HTMLParser
        
        results = []
        
        class DDGParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.in_result = False
                self.current_title = ""
                self.current_url = ""
                self.current_snippet = ""
            
            def handle_starttag(self, tag, attrs):
                attrs_dict = dict(attrs)
                if tag == "a" and "result__a" in attrs_dict.get("class", ""):
                    self.in_result = True
                    self.current_url = attrs_dict.get("href", "")
            
            def handle_data(self, data):
                if self.in_result:
                    self.current_title += data
            
            def handle_endtag(self, tag):
                if tag == "a" and self.in_result:
                    if self.current_title and self.current_url:
                        results.append({
                            "title": self.current_title.strip(),
                            "url": self.current_url
                        })
                    self.in_result = False
                    self.current_title = ""
                    self.current_url = ""
        
        parser = DDGParser()
        parser.feed(response.text)
        
        output = f"## Web Search Results (DuckDuckGo)\n\n**Query:** {query}\n\n"
        
        for i, result in enumerate(results[:max_results], 1):
            output += f"**{i}. [{result['title']}]({result['url']})**\n\n"
        
        if not results:
            output += "*No results found*"
        
        return ToolResult(content=[TextContent(text=output)])
        
    except Exception as e:
        logger.error(f"DuckDuckGo search error: {e}")
        return ToolResult(
            content=[TextContent(text=f"Search Error: {str(e)}")],
            isError=True
        )
