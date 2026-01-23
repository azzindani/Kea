"""
News Search Tool.

Search for news articles with date filtering.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

import httpx

from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger


logger = get_logger(__name__)


async def news_search_tool(arguments: dict) -> ToolResult:
    """
    Search for news articles.
    
    Args:
        arguments: Tool arguments containing:
            - query: Search query
            - days: Search within last N days (default 7)
            - max_results: Max results (default: hardware-aware)
    
    Returns:
        ToolResult with news results
    """
    from shared.hardware.detector import detect_hardware
    
    query = arguments.get("query", "")
    days = arguments.get("days", 7)
    hw = detect_hardware()
    max_results = arguments.get("max_results", hw.optimal_max_results())
    
    if not query:
        return ToolResult(
            content=[TextContent(text="Error: Query is required")],
            isError=True
        )
    
    # Try Tavily news search
    tavily_key = os.getenv("TAVILY_API_KEY", "")
    if tavily_key:
        return await _tavily_news_search(query, days, max_results, tavily_key)
    
    # Fallback to Google News RSS (no API key needed)
    return await _google_news_rss(query, max_results)


async def _tavily_news_search(query: str, days: int, max_results: int, api_key: str) -> ToolResult:
    """Search news using Tavily API."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "advanced",
                    "topic": "news",
                    "days": days,
                }
            )
            response.raise_for_status()
            data = response.json()
        
        output = f"## News Search Results\n\n"
        output += f"**Query:** {query}\n"
        output += f"**Period:** Last {days} days\n\n"
        
        for i, result in enumerate(data.get("results", []), 1):
            published = result.get("published_date", "Unknown date")
            output += f"**{i}. [{result.get('title', 'No title')}]({result.get('url', '')})**\n"
            output += f"*{published}*\n"
            output += f"{result.get('content', '')[:300]}...\n\n"
        
        if not data.get("results"):
            output += "*No news articles found*"
        
        return ToolResult(content=[TextContent(text=output)])
        
    except Exception as e:
        logger.error(f"Tavily news search error: {e}")
        return ToolResult(
            content=[TextContent(text=f"News Search Error: {str(e)}")],
            isError=True
        )


async def _google_news_rss(query: str, max_results: int) -> ToolResult:
    """Fallback to Google News RSS feed."""
    try:
        import urllib.parse
        
        encoded_query = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()
        
        # Parse RSS
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.text)
        
        output = f"## News Search Results (Google News)\n\n"
        output += f"**Query:** {query}\n\n"
        
        items = root.findall(".//item")[:max_results]
        
        for i, item in enumerate(items, 1):
            title = item.find("title")
            link = item.find("link")
            pub_date = item.find("pubDate")
            
            title_text = title.text if title is not None else "No title"
            link_text = link.text if link is not None else ""
            date_text = pub_date.text if pub_date is not None else ""
            
            output += f"**{i}. [{title_text}]({link_text})**\n"
            if date_text:
                output += f"*{date_text}*\n"
            output += "\n"
        
        if not items:
            output += "*No news articles found*"
        
        return ToolResult(content=[TextContent(text=output)])
        
    except Exception as e:
        logger.error(f"Google News RSS error: {e}")
        return ToolResult(
            content=[TextContent(text=f"News Search Error: {str(e)}")],
            isError=True
        )
