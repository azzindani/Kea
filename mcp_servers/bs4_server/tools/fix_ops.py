from mcp_servers.bs4_server.soup_manager import SoupManager
from typing import Optional
from urllib.parse import urljoin

async def make_links_absolute(base_url: str, soup_id: Optional[str] = None) -> str:
    """
    Convert relative URLs (href, src) to absolute URLs based on base_url.
    """
    soup = SoupManager.get_soup(soup_id)
    
    # Process href
    for tag in soup.find_all(["a", "link"], href=True):
        tag['href'] = urljoin(base_url, tag['href'])
        
    # Process src
    for tag in soup.find_all(["img", "script", "iframe", "source"], src=True):
        tag['src'] = urljoin(base_url, tag['src'])
        
    return f"Converted links to absolute using {base_url}"

async def normalize_structure(selector: str = "div", soup_id: Optional[str] = None) -> str:
    """
    Simplistic normalization: 
    - Convert <b>/<i> to <strong>/<em>
    - Unwrap useless spans (spans with no attributes)
    """
    soup = SoupManager.get_soup(soup_id)
    root = soup.select_one(selector) if selector != "body" else soup
    
    # b -> strong
    for t in root.find_all("b"):
        t.name = "strong"
        
    # i -> em
    for t in root.find_all("i"):
        t.name = "em"
        
    # unwrap empty spans
    spans = root.find_all("span")
    count = 0
    for s in spans:
        if not s.attrs:
            s.unwrap()
            count += 1
            
    return f"Normalized structure. Unwrapped {count} empty spans."
