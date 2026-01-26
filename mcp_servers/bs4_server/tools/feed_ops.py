from mcp_servers.bs4_server.soup_manager import SoupManager
from typing import Optional, List, Dict, Any

async def find_feed_links(soup_id: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Find RSS/Atom feed links in the document head.
    """
    soup = SoupManager.get_soup(soup_id)
    feeds = []
    
    # <link rel="alternate" type="application/rss+xml" href="...">
    links = soup.find_all("link", rel="alternate")
    for link in links:
        mime = link.get("type", "").lower()
        if "rss" in mime or "atom" in mime or "xml" in mime:
            feeds.append({
                "type": mime,
                "title": link.get("title", "Feed"),
                "href": link.get("href", "")
            })
            
    return feeds

async def extract_rss_items(soup_id: Optional[str] = None) -> List[Dict[str, str]]:
    """
    If the current soup IS an RSS/Atom XML feed, extract items.
    """
    soup = SoupManager.get_soup(soup_id)
    items = []
    
    # Try RSS <item>
    rss_items = soup.find_all("item")
    for item in rss_items:
        items.append({
            "title": item.title.get_text(strip=True) if item.title else "",
            "link": item.link.get_text(strip=True) if item.link else "",
            "description": item.description.get_text(strip=True) if item.description else "",
            "pubDate": item.pubdate.get_text(strip=True) if item.find("pubdate") else ""
        })
        
    # Try Atom <entry>
    atom_entries = soup.find_all("entry")
    for entry in atom_entries:
         items.append({
            "title": entry.title.get_text(strip=True) if entry.title else "",
            "link": entry.link["href"] if entry.link else "",
            "description": entry.summary.get_text(strip=True) if entry.find("summary") else (entry.content.get_text(strip=True) if entry.find("content") else ""),
            "pubDate": entry.updated.get_text(strip=True) if entry.find("updated") else ""
        })
        
    return items
