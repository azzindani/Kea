from __future__ import annotations
import os
from datetime import datetime
import httpx
import logging

logger = logging.getLogger(__name__)

async def news_search_tool(query: str, days: int = 7, max_results: int = 10) -> str:
    """Search for news articles."""
    if not query: return "Error: Query is required"
    
    # Try Tavily news search
    tavily_key = os.getenv("TAVILY_API_KEY", "")
    if tavily_key:
        return await _tavily_news_search(query, days, max_results, tavily_key)
    
    # Fallback to Google News RSS
    return await _google_news_rss(query, max_results)

async def _tavily_news_search(query: str, days: int, max_results: int, api_key: str) -> str:
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
        
        output = f"## News Search Results\n\n**Query:** {query}\n**Period:** Last {days} days\n\n"
        for i, result in enumerate(data.get("results", []), 1):
            published = result.get("published_date", "Unknown date")
            output += f"**{i}. [{result.get('title', 'No title')}]({result.get('url', '')})**\n"
            output += f"*{published}*\n{result.get('content', '')[:300]}...\n\n"
        
        if not data.get("results"): output += "*No news articles found*"
        return output
    except Exception as e:
        return f"News Search Error: {str(e)}"

async def _google_news_rss(query: str, max_results: int) -> str:
    try:
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()
        
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.text)
        
        output = f"## News Search Results (Google News)\n\n**Query:** {query}\n\n"
        items = root.findall(".//item")[:max_results]
        
        for i, item in enumerate(items, 1):
            title = item.find("title")
            link = item.find("link")
            pub_date = item.find("pubDate")
            
            title_text = title.text if title is not None else "No title"
            link_text = link.text if link is not None else ""
            date_text = pub_date.text if pub_date is not None else ""
            
            output += f"**{i}. [{title_text}]({link_text})**\n"
            if date_text: output += f"*{date_text}*\n"
            output += "\n"
        
        if not items: output += "*No news articles found*"
        return output
    except Exception as e:
        return f"News Search Error: {str(e)}"
