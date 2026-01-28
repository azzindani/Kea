import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

async def link_extractor(url: str, filter_external: bool = False, classify: bool = False) -> str:
    """Extract all links from a webpage."""
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
    
    return result
