"""
Web Crawler MCP Server.

Provides tools for web crawling and content discovery:
- Recursive crawling with depth control
- Sitemap parsing
- Link extraction
- Content classification
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin, urlparse
import asyncio

from shared.mcp.server_base import MCPServerBase
from shared.mcp.protocol import Tool, ToolInputSchema, ToolResult, TextContent
from shared.logging import get_logger


logger = get_logger(__name__)


class CrawlerServer(MCPServerBase):
    """MCP server for web crawling operations."""
    
    def __init__(self) -> None:
        super().__init__(name="crawler_server")
    
    def get_tools(self) -> list[Tool]:
        """Return available tools."""
        return [
            Tool(
                name="web_crawler",
                description="Recursively crawl a website with depth control",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "start_url": {"type": "string", "description": "Starting URL to crawl"},
                        "max_depth": {"type": "integer", "description": "Maximum crawl depth (1-5)"},
                        "max_pages": {"type": "integer", "description": "Maximum pages to crawl (1-100)"},
                        "same_domain": {"type": "boolean", "description": "Stay on same domain only"},
                        "delay": {"type": "number", "description": "Delay between requests in seconds"},
                    },
                    required=["start_url"],
                ),
            ),
            Tool(
                name="sitemap_parser",
                description="Parse website sitemap for URL discovery",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "url": {"type": "string", "description": "Sitemap URL or website root"},
                        "filter_pattern": {"type": "string", "description": "Regex pattern to filter URLs"},
                    },
                    required=["url"],
                ),
            ),
            Tool(
                name="link_extractor",
                description="Extract all links from a webpage",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "url": {"type": "string", "description": "Page URL to extract links from"},
                        "filter_external": {"type": "boolean", "description": "Filter out external links"},
                        "classify": {"type": "boolean", "description": "Classify link types"},
                    },
                    required=["url"],
                ),
            ),
            Tool(
                name="robots_checker",
                description="Check robots.txt for allowed/disallowed paths",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "url": {"type": "string", "description": "Website URL"},
                        "check_path": {"type": "string", "description": "Specific path to check"},
                    },
                    required=["url"],
                ),
            ),
            Tool(
                name="domain_analyzer",
                description="Analyze domain for crawling strategy",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "url": {"type": "string", "description": "Website URL to analyze"},
                    },
                    required=["url"],
                ),
            ),
        ]
    
    async def handle_tool_call(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        """Handle tool call."""
        try:
            if name == "web_crawler":
                return await self._handle_crawler(arguments)
            elif name == "sitemap_parser":
                return await self._handle_sitemap(arguments)
            elif name == "link_extractor":
                return await self._handle_links(arguments)
            elif name == "robots_checker":
                return await self._handle_robots(arguments)
            elif name == "domain_analyzer":
                return await self._handle_domain_analysis(arguments)
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
    
    async def _handle_crawler(self, args: dict) -> ToolResult:
        """Crawl website recursively."""
        import httpx
        from bs4 import BeautifulSoup
        
        start_url = args["start_url"]
        # Allow unlimited depth - user/LLM can specify any value
        max_depth = args.get("max_depth", 5)  # Default 5, no upper limit
        max_pages = args.get("max_pages", 100)  # Default 100, can go to 1000+
        same_domain = args.get("same_domain", True)
        delay = args.get("delay", 0.5)  # Faster default
        
        base_domain = urlparse(start_url).netloc
        
        visited = set()
        pages = []
        
        async def crawl(url: str, depth: int):
            if url in visited or len(visited) >= max_pages or depth > max_depth:
                return
            
            visited.add(url)
            
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    response = await client.get(url, follow_redirects=True)
                    
                    if response.status_code != 200:
                        return
                    
                    content_type = response.headers.get("content-type", "")
                    if "text/html" not in content_type:
                        return
                    
                    soup = BeautifulSoup(response.text, "html.parser")
                    
                    title = soup.title.string if soup.title else "No title"
                    
                    # Extract text preview
                    text = soup.get_text(separator=" ", strip=True)[:200]
                    
                    pages.append({
                        "url": url,
                        "title": title,
                        "depth": depth,
                        "preview": text,
                    })
                    
                    # Find links
                    if depth < max_depth:
                        await asyncio.sleep(delay)  # Rate limiting
                        
                        for a in soup.find_all("a", href=True):
                            next_url = urljoin(url, a["href"])
                            next_parsed = urlparse(next_url)
                            
                            # Filter
                            if same_domain and next_parsed.netloc != base_domain:
                                continue
                            if next_parsed.scheme not in ["http", "https"]:
                                continue
                            if next_url.endswith(('.pdf', '.jpg', '.png', '.gif', '.zip')):
                                continue
                            
                            await crawl(next_url, depth + 1)
                            
            except Exception as e:
                logger.debug(f"Crawl error {url}: {e}")
        
        await crawl(start_url, 1)
        
        result = f"# 🕷️ Web Crawler Results\n\n"
        result += f"**Start URL**: {start_url}\n"
        result += f"**Max Depth**: {max_depth}\n"
        result += f"**Pages Found**: {len(pages)}\n\n"
        
        result += "## Pages\n\n"
        for page in pages:
            result += f"### [{page['title']}]({page['url']})\n"
            result += f"- Depth: {page['depth']}\n"
            result += f"- Preview: {page['preview'][:100]}...\n\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_sitemap(self, args: dict) -> ToolResult:
        """Parse sitemap."""
        import httpx
        import re
        from xml.etree import ElementTree
        
        url = args["url"]
        filter_pattern = args.get("filter_pattern")
        
        # Try to find sitemap
        parsed = urlparse(url)
        sitemap_urls = [
            url if url.endswith(".xml") else None,
            f"{parsed.scheme}://{parsed.netloc}/sitemap.xml",
            f"{parsed.scheme}://{parsed.netloc}/sitemap_index.xml",
        ]
        
        urls = []
        
        async with httpx.AsyncClient(timeout=30) as client:
            for sitemap_url in filter(None, sitemap_urls):
                try:
                    response = await client.get(sitemap_url)
                    if response.status_code == 200:
                        root = ElementTree.fromstring(response.text)
                        
                        # Handle both sitemap and sitemap index
                        for elem in root.iter():
                            if elem.tag.endswith("loc"):
                                urls.append(elem.text)
                        break
                except Exception:
                    continue
        
        # Apply filter
        if filter_pattern:
            pattern = re.compile(filter_pattern)
            urls = [u for u in urls if pattern.search(u)]
        
        result = f"# 🗺️ Sitemap Parser\n\n"
        result += f"**Source**: {url}\n"
        result += f"**URLs Found**: {len(urls)}\n\n"
        
        result += "## URLs\n\n"
        for u in urls[:50]:
            result += f"- {u}\n"
        
        if len(urls) > 50:
            result += f"\n... and {len(urls) - 50} more\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_links(self, args: dict) -> ToolResult:
        """Extract links from page."""
        import httpx
        from bs4 import BeautifulSoup
        
        url = args["url"]
        filter_external = args.get("filter_external", False)
        classify = args.get("classify", False)
        
        base_domain = urlparse(url).netloc
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
        
        links = []
        for a in soup.find_all("a", href=True):
            href = urljoin(url, a["href"])
            text = a.get_text(strip=True)[:50]
            
            parsed = urlparse(href)
            is_external = parsed.netloc != base_domain
            
            if filter_external and is_external:
                continue
            
            link_info = {
                "url": href,
                "text": text,
                "external": is_external,
            }
            
            if classify:
                # Classify link type
                if parsed.path.endswith(".pdf"):
                    link_info["type"] = "pdf"
                elif parsed.path.endswith((".jpg", ".png", ".gif")):
                    link_info["type"] = "image"
                elif "/blog/" in parsed.path or "/news/" in parsed.path:
                    link_info["type"] = "article"
                elif "/product" in parsed.path:
                    link_info["type"] = "product"
                else:
                    link_info["type"] = "page"
            
            links.append(link_info)
        
        result = f"# 🔗 Link Extractor\n\n"
        result += f"**Source**: {url}\n"
        result += f"**Links Found**: {len(links)}\n\n"
        
        if classify:
            # Group by type
            by_type = {}
            for link in links:
                t = link.get("type", "other")
                if t not in by_type:
                    by_type[t] = []
                by_type[t].append(link)
            
            for link_type, type_links in by_type.items():
                result += f"## {link_type.title()} ({len(type_links)})\n\n"
                for link in type_links[:10]:
                    result += f"- [{link['text'] or 'No text'}]({link['url']})\n"
                result += "\n"
        else:
            result += "## Links\n\n"
            for link in links[:50]:
                external = " 🌐" if link["external"] else ""
                result += f"- [{link['text'] or 'No text'}]({link['url']}){external}\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_robots(self, args: dict) -> ToolResult:
        """Check robots.txt."""
        import httpx
        
        url = args["url"]
        check_path = args.get("check_path")
        
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(robots_url)
        
        result = f"# 🤖 Robots.txt Checker\n\n"
        result += f"**URL**: {robots_url}\n\n"
        
        if response.status_code == 200:
            result += "## Content\n```\n"
            result += response.text[:3000]
            result += "\n```\n"
            
            if check_path:
                # Simple check
                disallowed = any(
                    f"Disallow: {check_path}" in response.text or
                    f"Disallow: *" in response.text
                )
                result += f"\n## Path Check: {check_path}\n"
                result += f"Status: {'🚫 Disallowed' if disallowed else '✅ Allowed'}\n"
        else:
            result += "No robots.txt found (all paths allowed)\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_domain_analysis(self, args: dict) -> ToolResult:
        """Analyze domain."""
        import httpx
        from bs4 import BeautifulSoup
        
        url = args["url"]
        parsed = urlparse(url)
        domain = parsed.netloc
        
        result = f"# 🔍 Domain Analysis\n\n"
        result += f"**Domain**: {domain}\n\n"
        
        async with httpx.AsyncClient(timeout=30) as client:
            # Check main page
            try:
                response = await client.get(url)
                soup = BeautifulSoup(response.text, "html.parser")
                
                result += "## Page Info\n\n"
                result += f"- Title: {soup.title.string if soup.title else 'No title'}\n"
                result += f"- Status: {response.status_code}\n"
                
                # Count elements
                result += f"- Links: {len(soup.find_all('a'))}\n"
                result += f"- Images: {len(soup.find_all('img'))}\n"
                result += f"- Forms: {len(soup.find_all('form'))}\n"
                
            except Exception as e:
                result += f"Error: {e}\n"
            
            # Check robots.txt
            try:
                robots = await client.get(f"{parsed.scheme}://{domain}/robots.txt")
                result += f"\n## Robots.txt\n\n"
                result += f"- Exists: {'Yes' if robots.status_code == 200 else 'No'}\n"
            except Exception:
                pass
            
            # Check sitemap
            try:
                sitemap = await client.get(f"{parsed.scheme}://{domain}/sitemap.xml")
                result += f"\n## Sitemap\n\n"
                result += f"- Exists: {'Yes' if sitemap.status_code == 200 else 'No'}\n"
            except Exception:
                pass
        
        return ToolResult(content=[TextContent(text=result)])


# Export tool functions
async def web_crawler_tool(args: dict) -> ToolResult:
    server = CrawlerServer()
    return await server._handle_crawler(args)

async def sitemap_parser_tool(args: dict) -> ToolResult:
    server = CrawlerServer()
    return await server._handle_sitemap(args)

async def link_extractor_tool(args: dict) -> ToolResult:
    server = CrawlerServer()
    return await server._handle_links(args)


if __name__ == "__main__":
    import asyncio
    
    async def main():
        server = CrawlerServer()
        await server.run()
        
    asyncio.run(main())
