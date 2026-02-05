import asyncio
import random
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import List, Dict, Any, Optional

async def human_like_search(query: str, max_sites: int = 5, min_delay: float = 1.0, max_delay: float = 3.0, focus_domains: List[str] = []) -> str:
    """Search and browse like a human researcher with natural delays."""
    max_sites = min(max_sites, 10)
    
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
    
    return result

async def multi_site_browse(urls: List[str], extract: str = "summary", max_concurrent: int = 10) -> str:
    """Browse multiple sites in parallel (rate-limited)."""
    urls = urls[:50]  # Allow up to 50 URLs
    max_concurrent = min(max_concurrent, 20)  # Up to 20 parallel
    
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
    
    return result
