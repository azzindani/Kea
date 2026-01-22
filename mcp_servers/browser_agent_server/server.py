"""
Browser Agent MCP Server.

Intelligent browsing agent that mimics human search behavior:
- Human-like browsing with delays
- Source credibility validation
- Multi-tab parallel browsing
- Search memory and logging
"""

from __future__ import annotations

from typing import Any
import asyncio
import random
from urllib.parse import urlparse
import hashlib

from shared.mcp.server_base import MCPServerBase
from shared.mcp.protocol import Tool, ToolInputSchema, ToolResult, TextContent
from shared.logging import get_logger


logger = get_logger(__name__)


# In-memory search memory (would be persisted to HuggingFace in production)
SEARCH_MEMORY: dict[str, dict] = {}


class BrowserAgentServer(MCPServerBase):
    """MCP server for intelligent browsing operations."""
    
    def __init__(self) -> None:
        super().__init__(name="browser_agent_server")
    
    def get_tools(self) -> list[Tool]:
        """Return available tools."""
        return [
            Tool(
                name="human_like_search",
                description="Search and browse like a human researcher with natural delays",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "query": {"type": "string", "description": "Search query"},
                        "max_sites": {"type": "integer", "description": "Maximum sites to visit (1-10)"},
                        "min_delay": {"type": "number", "description": "Minimum delay between requests (seconds)"},
                        "max_delay": {"type": "number", "description": "Maximum delay between requests (seconds)"},
                        "focus_domains": {"type": "array", "description": "Preferred domains to prioritize"},
                    },
                    required=["query"],
                ),
            ),
            Tool(
                name="source_validator",
                description="Validate if a source/website is credible and legitimate",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "url": {"type": "string", "description": "URL to validate"},
                        "check_type": {"type": "string", "description": "Check: basic, thorough, academic"},
                    },
                    required=["url"],
                ),
            ),
            Tool(
                name="domain_scorer",
                description="Score domain trustworthiness for research",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "domains": {"type": "array", "description": "List of domains to score"},
                    },
                    required=["domains"],
                ),
            ),
            Tool(
                name="search_memory_add",
                description="Add a search result to memory for future reference",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "query": {"type": "string", "description": "Original search query"},
                        "url": {"type": "string", "description": "URL of result"},
                        "title": {"type": "string", "description": "Page title"},
                        "summary": {"type": "string", "description": "Content summary"},
                        "relevance_score": {"type": "number", "description": "Relevance 0-1"},
                        "credibility_score": {"type": "number", "description": "Credibility 0-1"},
                    },
                    required=["query", "url"],
                ),
            ),
            Tool(
                name="search_memory_recall",
                description="Recall previous search results from memory",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "query": {"type": "string", "description": "Query to search memory for"},
                        "min_relevance": {"type": "number", "description": "Minimum relevance score"},
                    },
                    required=["query"],
                ),
            ),
            Tool(
                name="multi_site_browse",
                description="Browse multiple sites in parallel (rate-limited)",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "urls": {"type": "array", "description": "URLs to browse"},
                        "extract": {"type": "string", "description": "What to extract: text, links, summary"},
                        "max_concurrent": {"type": "integer", "description": "Max parallel requests"},
                    },
                    required=["urls"],
                ),
            ),
        ]
    
    async def handle_tool_call(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        """Handle tool call."""
        try:
            if name == "human_like_search":
                return await self._handle_human_search(arguments)
            elif name == "source_validator":
                return await self._handle_validator(arguments)
            elif name == "domain_scorer":
                return await self._handle_domain_scorer(arguments)
            elif name == "search_memory_add":
                return await self._handle_memory_add(arguments)
            elif name == "search_memory_recall":
                return await self._handle_memory_recall(arguments)
            elif name == "multi_site_browse":
                return await self._handle_multi_browse(arguments)
            else:
                return ToolResult(
                    content=[TextContent(text=f"Unknown tool: {name}")],
                    isError=True,
                )
        except Exception as e:
            logger.error(f"Tool {name} failed: {e}")
            return ToolResult(
                content=[TextContent(text=f"Error: {str(e)}")],
                isError=True,
            )
    
    async def _handle_human_search(self, args: dict) -> ToolResult:
        """Search and browse like a human."""
        import httpx
        from bs4 import BeautifulSoup
        
        query = args["query"]
        max_sites = min(args.get("max_sites", 5), 10)
        min_delay = args.get("min_delay", 1.0)
        max_delay = args.get("max_delay", 3.0)
        focus_domains = args.get("focus_domains", [])
        
        result = f"# 🔍 Human-Like Research Search\n\n"
        result += f"**Query**: {query}\n"
        result += f"**Max Sites**: {max_sites}\n"
        result += f"**Delay Range**: {min_delay}-{max_delay}s\n\n"
        
        # Simulate search results (would use real search API)
        async with httpx.AsyncClient(timeout=30) as client:
            # DuckDuckGo HTML search (simple, no API key)
            try:
                search_resp = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query},
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                )
                soup = BeautifulSoup(search_resp.text, "html.parser")
                
                links = []
                for a in soup.select(".result__a")[:max_sites]:
                    href = a.get("href", "")
                    title = a.get_text(strip=True)
                    if href and title:
                        links.append({"url": href, "title": title})
                
            except Exception as e:
                result += f"Search error: {e}\n"
                links = []
        
        result += f"## Found {len(links)} Results\n\n"
        
        visited = []
        for i, link in enumerate(links):
            # Human-like delay
            delay = random.uniform(min_delay, max_delay)
            await asyncio.sleep(delay)
            
            url = link["url"]
            title = link["title"]
            domain = urlparse(url).netloc
            
            # Check if in focus domains
            is_focus = any(fd in domain for fd in focus_domains)
            
            result += f"### {i+1}. {title[:60]}\n"
            result += f"- **URL**: {url[:80]}...\n" if len(url) > 80 else f"- **URL**: {url}\n"
            result += f"- **Domain**: {domain}\n"
            result += f"- **Focus Domain**: {'✅ Yes' if is_focus else '❌ No'}\n"
            result += f"- **Delay Used**: {delay:.1f}s\n\n"
            
            visited.append({
                "url": url,
                "title": title,
                "domain": domain,
                "is_focus": is_focus,
            })
        
        result += f"## Summary\n\n"
        result += f"- Sites visited: {len(visited)}\n"
        result += f"- Focus domain matches: {sum(1 for v in visited if v['is_focus'])}\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_validator(self, args: dict) -> ToolResult:
        """Validate source credibility."""
        import httpx
        
        url = args.get("url")
        if not url:
             return ToolResult(content=[TextContent(text="Error: 'url' argument is required")], isError=True)
        check_type = args.get("check_type", "basic")
        
        parsed = urlparse(url)
        domain = parsed.netloc
        
        result = f"# ✅ Source Validation\n\n"
        result += f"**URL**: {url}\n"
        result += f"**Domain**: {domain}\n"
        result += f"**Check Type**: {check_type}\n\n"
        
        # Credibility indicators
        indicators = {}
        
        # Domain age and trust signals
        # Academic/government TLDs
        if domain.endswith(('.edu', '.gov', '.ac.uk', '.go.id')):
            indicators["tld_trust"] = ("High", "Government/Academic TLD")
        elif domain.endswith(('.org', '.int')):
            indicators["tld_trust"] = ("Medium-High", "Organization TLD")
        else:
            indicators["tld_trust"] = ("Standard", "Commercial TLD")
        
        # Known authoritative domains
        authoritative = [
            'nature.com', 'science.org', 'sciencedirect.com',
            'pubmed.ncbi.nlm.nih.gov', 'arxiv.org', 'springer.com',
            'reuters.com', 'bbc.com', 'nytimes.com', 'wsj.com',
            'sec.gov', 'imf.org', 'worldbank.org', 'who.int',
        ]
        
        is_authoritative = any(auth in domain for auth in authoritative)
        indicators["authoritative"] = ("Yes" if is_authoritative else "No", "Known authoritative source")
        
        # HTTPS check
        indicators["https"] = ("Yes" if parsed.scheme == "https" else "No", "Secure connection")
        
        # Calculate score
        score = 0.5  # Base score
        if indicators["tld_trust"][0] == "High":
            score += 0.3
        elif indicators["tld_trust"][0] == "Medium-High":
            score += 0.15
        if is_authoritative:
            score += 0.2
        if parsed.scheme == "https":
            score += 0.1
        
        score = min(1.0, score)
        
        result += "## Credibility Indicators\n\n"
        result += "| Indicator | Value | Note |\n|-----------|-------|------|\n"
        for name, (value, note) in indicators.items():
            result += f"| {name} | {value} | {note} |\n"
        
        result += f"\n## Overall Score: {score:.2f}/1.0\n\n"
        
        if score >= 0.8:
            result += "🟢 **Highly Credible** - Authoritative source\n"
        elif score >= 0.6:
            result += "🟡 **Moderately Credible** - Verify claims\n"
        else:
            result += "🔴 **Low Credibility** - Cross-reference required\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_domain_scorer(self, args: dict) -> ToolResult:
        """Score domain trustworthiness."""
        domains = args["domains"]
        
        result = "# 🏆 Domain Trust Scores\n\n"
        
        # Trust database
        trust_db = {
            # Academic
            'nature.com': 0.95, 'science.org': 0.95, 'arxiv.org': 0.90,
            'pubmed.ncbi.nlm.nih.gov': 0.95, 'ncbi.nlm.nih.gov': 0.95,
            'sciencedirect.com': 0.90, 'springer.com': 0.90,
            # Government
            'sec.gov': 0.95, 'data.gov': 0.90, 'irs.gov': 0.95,
            'who.int': 0.95, 'worldbank.org': 0.90, 'imf.org': 0.90,
            # News
            'reuters.com': 0.85, 'bbc.com': 0.85, 'nytimes.com': 0.80,
            'wsj.com': 0.80, 'ft.com': 0.80,
            # General
            'wikipedia.org': 0.70, 'britannica.com': 0.85,
        }
        
        result += "| Domain | Trust Score | Category |\n|--------|-------------|----------|\n"
        
        for domain in domains:
            domain_clean = domain.lower().replace("www.", "")
            
            if domain_clean in trust_db:
                score = trust_db[domain_clean]
            elif any(tld in domain_clean for tld in ['.edu', '.gov']):
                score = 0.85
            elif any(tld in domain_clean for tld in ['.org']):
                score = 0.70
            else:
                score = 0.50
            
            # Categorize
            if score >= 0.9:
                category = "🟢 Highly Trusted"
            elif score >= 0.7:
                category = "🟡 Trusted"
            elif score >= 0.5:
                category = "🟠 Moderate"
            else:
                category = "🔴 Low Trust"
            
            result += f"| {domain} | {score:.2f} | {category} |\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_memory_add(self, args: dict) -> ToolResult:
        """Add search result to memory."""
        query = args.get("query")
        url = args.get("url")
        
        if not query or not url:
            return ToolResult(content=[TextContent(text="Error: 'query' and 'url' are required")], isError=True)
        title = args.get("title", "")
        summary = args.get("summary", "")
        relevance = args.get("relevance_score", 0.5)
        credibility = args.get("credibility_score", 0.5)
        
        # Create memory key
        key = hashlib.md5(url.encode()).hexdigest()[:12]
        
        entry = {
            "query": query,
            "url": url,
            "title": title,
            "summary": summary,
            "relevance": relevance,
            "credibility": credibility,
            "timestamp": asyncio.get_event_loop().time(),
        }
        
        SEARCH_MEMORY[key] = entry
        
        result = f"# 🧠 Memory Updated\n\n"
        result += f"**Key**: {key}\n"
        result += f"**URL**: {url}\n"
        result += f"**Query**: {query}\n"
        result += f"**Relevance**: {relevance:.2f}\n"
        result += f"**Credibility**: {credibility:.2f}\n\n"
        result += f"Total memories: {len(SEARCH_MEMORY)}\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_memory_recall(self, args: dict) -> ToolResult:
        """Recall from search memory."""
        query = args["query"]
        min_relevance = args.get("min_relevance", 0.0)
        
        query_lower = query.lower()
        
        result = f"# 🧠 Memory Recall\n\n"
        result += f"**Query**: {query}\n"
        result += f"**Min Relevance**: {min_relevance}\n\n"
        
        matches = []
        for key, entry in SEARCH_MEMORY.items():
            # Simple text matching
            if (query_lower in entry.get("query", "").lower() or 
                query_lower in entry.get("title", "").lower() or
                query_lower in entry.get("summary", "").lower()):
                if entry.get("relevance", 0) >= min_relevance:
                    matches.append((key, entry))
        
        result += f"## Found {len(matches)} Memories\n\n"
        
        for key, entry in matches:
            result += f"### {entry.get('title', 'No title')}\n"
            result += f"- **URL**: {entry.get('url')}\n"
            result += f"- **Original Query**: {entry.get('query')}\n"
            result += f"- **Relevance**: {entry.get('relevance', 0):.2f}\n"
            result += f"- **Credibility**: {entry.get('credibility', 0):.2f}\n\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_multi_browse(self, args: dict) -> ToolResult:
        """Browse multiple sites in parallel."""
        import httpx
        from bs4 import BeautifulSoup
        
        urls = args.get("urls", [])
        if not urls:
             return ToolResult(content=[TextContent(text="Error: 'urls' argument is required")], isError=True)
        urls = urls[:50]  # Allow up to 50 URLs
        extract = args.get("extract", "summary")
        max_concurrent = min(args.get("max_concurrent", 10), 20)  # Up to 20 parallel
        
        result = f"# 🌐 Multi-Site Browse\n\n"
        result += f"**URLs**: {len(urls)}\n"
        result += f"**Concurrent**: {max_concurrent}\n\n"
        
        async def fetch_one(url: str) -> dict:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(url, follow_redirects=True)
                    soup = BeautifulSoup(resp.text, "html.parser")
                    
                    title = soup.title.string if soup.title else "No title"
                    
                    if extract == "text":
                        content = soup.get_text(separator=" ", strip=True)[:500]
                    elif extract == "links":
                        content = [a.get("href") for a in soup.find_all("a", href=True)[:10]]
                    else:  # summary
                        # Get meta description or first paragraph
                        meta = soup.find("meta", {"name": "description"})
                        if meta:
                            content = meta.get("content", "")[:200]
                        else:
                            p = soup.find("p")
                            content = p.get_text(strip=True)[:200] if p else ""
                    
                    return {"url": url, "title": title, "content": content, "success": True}
            except Exception as e:
                return {"url": url, "error": str(e), "success": False}
        
        # Fetch with concurrency limit
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_with_limit(url):
            async with semaphore:
                await asyncio.sleep(random.uniform(0.5, 1.5))  # Rate limit
                return await fetch_one(url)
        
        results_list = await asyncio.gather(*[fetch_with_limit(u) for u in urls])
        
        result += "## Results\n\n"
        for r in results_list:
            if r["success"]:
                result += f"### ✅ {r.get('title', 'No title')[:50]}\n"
                result += f"- **URL**: {r['url']}\n"
                if isinstance(r.get("content"), list):
                    result += f"- **Links**: {len(r['content'])} found\n"
                else:
                    result += f"- **Content**: {r.get('content', '')[:100]}...\n"
            else:
                result += f"### ❌ Failed: {r['url']}\n"
                result += f"- **Error**: {r.get('error')}\n"
            result += "\n"
        
        return ToolResult(content=[TextContent(text=result)])


# Export tool functions
async def human_like_search_tool(args: dict) -> ToolResult:
    server = BrowserAgentServer()
    return await server._handle_human_search(args)

async def source_validator_tool(args: dict) -> ToolResult:
    server = BrowserAgentServer()
    return await server._handle_validator(args)


if __name__ == "__main__":
    import asyncio
    
    async def main():
        server = BrowserAgentServer()
        await server.run()
        
    asyncio.run(main())
