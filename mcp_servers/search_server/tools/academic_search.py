"""
Academic Search Tool.

Search academic papers from arXiv and Semantic Scholar.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from shared.mcp.protocol import ToolResult, TextContent
from shared.logging.main import get_logger


logger = get_logger(__name__)


async def academic_search_tool(arguments: dict) -> ToolResult:
    """
    Search academic papers.
    
    Args:
        arguments: Tool arguments containing:
            - query: Search query
            - max_results: Max results (default: hardware-aware)
            - source: arxiv, semantic_scholar, or both (default: both)
    
    Returns:
        ToolResult with paper results
    """
    from shared.hardware.detector import detect_hardware
    
    query = arguments.get("query", "")
    hw = detect_hardware()
    max_results = arguments.get("max_results", hw.optimal_max_results())
    source = arguments.get("source", "both")
    
    if not query:
        return ToolResult(
            content=[TextContent(text="Error: Query is required")],
            isError=True
        )
    
    results = []
    
    # Search arXiv
    if source in ["arxiv", "both"]:
        arxiv_results = await _search_arxiv(query, max_results)
        results.extend(arxiv_results)
    
    # Search Semantic Scholar
    if source in ["semantic_scholar", "both"]:
        ss_results = await _search_semantic_scholar(query, max_results)
        results.extend(ss_results)
    
    # Deduplicate by title similarity
    seen_titles = set()
    unique_results = []
    for r in results:
        title_key = r["title"].lower()[:50]
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_results.append(r)
    
    # Build output
    output = f"## Academic Search Results\n\n"
    output += f"**Query:** {query}\n"
    output += f"**Results:** {len(unique_results)}\n\n"
    
    for i, paper in enumerate(unique_results[:max_results], 1):
        output += f"### {i}. {paper['title']}\n\n"
        output += f"**Authors:** {paper.get('authors', 'Unknown')}\n"
        output += f"**Year:** {paper.get('year', 'N/A')}\n"
        output += f"**Source:** {paper.get('source', 'Unknown')}\n"
        
        if paper.get("url"):
            output += f"**URL:** [{paper['url']}]({paper['url']})\n"
        
        if paper.get("abstract"):
            abstract = paper["abstract"]
            output += f"\n> {abstract}\n"
        
        output += "\n---\n\n"
    
    if not unique_results:
        output += "*No papers found*"
    
    return ToolResult(content=[TextContent(text=output)])


async def _search_arxiv(query: str, max_results: int) -> list[dict]:
    """Search arXiv API."""
    try:
        import urllib.parse
        
        encoded_query = urllib.parse.quote(query)
        url = f"https://export.arxiv.org/api/query?search_query=all:{encoded_query}&start=0&max_results={max_results}"
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()
        
        # Parse Atom XML
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.text)
        
        # Namespace
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        
        results = []
        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns)
            summary = entry.find("atom:summary", ns)
            published = entry.find("atom:published", ns)
            
            authors = []
            for author in entry.findall("atom:author", ns):
                name = author.find("atom:name", ns)
                if name is not None:
                    authors.append(name.text)
            
            link = None
            for l in entry.findall("atom:link", ns):
                if l.get("type") == "text/html":
                    link = l.get("href")
                    break
            
            if link is None:
                id_elem = entry.find("atom:id", ns)
                if id_elem is not None:
                    link = id_elem.text
            
            year = ""
            if published is not None and published.text:
                year = published.text[:4]
            
            results.append({
                "title": title.text.strip() if title is not None else "Unknown",
                "authors": ", ".join(authors),
                "abstract": summary.text.strip() if summary is not None else "",
                "year": year,
                "url": link or "",
                "source": "arXiv",
            })
        
        return results
        
    except Exception as e:
        logger.error(f"arXiv search error: {e}")
        return []


async def _search_semantic_scholar(query: str, max_results: int) -> list[dict]:
    """Search Semantic Scholar API."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params={
                    "query": query,
                    "limit": max_results,
                    "fields": "title,authors,year,abstract,url",
                }
            )
            response.raise_for_status()
            data = response.json()
        
        results = []
        for paper in data.get("data", []):
            authors = paper.get("authors", [])
            author_names = [a.get("name", "") for a in authors[:3]]
            
            results.append({
                "title": paper.get("title", "Unknown"),
                "authors": ", ".join(author_names),
                "abstract": paper.get("abstract", ""),
                "year": str(paper.get("year", "")),
                "url": paper.get("url", ""),
                "source": "Semantic Scholar",
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Semantic Scholar search error: {e}")
        return []
