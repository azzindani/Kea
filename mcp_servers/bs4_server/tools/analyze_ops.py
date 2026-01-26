from mcp_servers.bs4_server.soup_manager import SoupManager
from typing import Optional, Dict, List, Any
from urllib.parse import urlparse

async def analyze_links(soup_id: Optional[str] = None, base_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Categorize links into Internal, External, Anchors, and Mailto.
    """
    soup = SoupManager.get_soup(soup_id)
    links = soup.find_all("a", href=True)
    
    internal = []
    external = []
    anchors = []
    mailto = []
    
    base_domain = urlparse(base_url).netloc if base_url else ""
    
    for a in links:
        href = a['href']
        if href.startswith("#"):
            anchors.append(href)
        elif href.startswith("mailto:"):
            mailto.append(href)
        elif not href.startswith("http"):
            internal.append(href)
        else:
            domain = urlparse(href).netloc
            if base_domain and domain == base_domain:
                internal.append(href)
            else:
                external.append(href)
                
    return {
        "total": len(links),
        "internal_count": len(internal),
        "external_count": len(external),
        "anchor_count": len(anchors),
        "mailto_count": len(mailto),
        "external_domains": list(set([urlparse(u).netloc for u in external]))[:20]  # Sample
    }

async def tag_frequency(soup_id: Optional[str] = None) -> Dict[str, int]:
    """
    Count frequency of each tag type.
    """
    soup = SoupManager.get_soup(soup_id)
    from collections import Counter
    tags = [tag.name for tag in soup.find_all(True)]
    return dict(Counter(tags))

async def get_text_density(selector: str = "body", soup_id: Optional[str] = None) -> float:
    """
    Calculate text-to-tag ratio (Text Density).
    Useful for identifying content-heavy areas.
    """
    soup = SoupManager.get_soup(soup_id)
    root = soup.select_one(selector)
    if not root:
        return 0.0
        
    text_len = len(root.get_text(strip=True))
    tag_count = len(root.find_all(True))
    
    if tag_count == 0:
        return 0.0
        
    return round(text_len / tag_count, 2)
