import asyncio
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree
import re
from typing import Optional

async def web_crawler(start_url: str, max_depth: int = 5, max_pages: int = 100, same_domain: bool = True, delay: float = 0.5) -> str:
    """Recursively crawl a website with depth control."""
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
            pass
    
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
    
    return result

async def sitemap_parser(url: str, filter_pattern: Optional[str] = None) -> str:
    """Parse website sitemap for URL discovery."""
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
    
    return result
