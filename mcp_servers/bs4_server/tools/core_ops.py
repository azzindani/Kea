from mcp_servers.bs4_server.soup_manager import SoupManager
from typing import Dict, Any, Optional
import structlog

logger = structlog.get_logger()

async def parse_html(html: str, parser: str = "lxml") -> str:
    """Parse raw HTML string and return Soup ID."""
    return SoupManager.load_html(html, parser)

async def load_file(path: str, parser: str = "lxml") -> str:
    """Load HTML from local file."""
    return SoupManager.load_file(path, parser)

async def save_file(soup_id: str, path: str) -> str:
    """Save current soup state to file."""
    soup = SoupManager.get_soup(soup_id)
    with open(path, "w", encoding="utf-8") as f:
        f.write(str(soup))
    return f"Saved soup {soup_id} to {path}"

async def prettify_soup(soup_id: Optional[str] = None) -> str:
    """Return formatted HTML string."""
    soup = SoupManager.get_soup(soup_id)
    return soup.prettify()

async def get_soup_stats(soup_id: Optional[str] = None) -> Dict[str, Any]:
    """Get statistics about the parsed document."""
    soup = SoupManager.get_soup(soup_id)
    return {
        "tags_count": len(soup.find_all()),
        "text_length": len(soup.get_text()),
        "has_body": bool(soup.body),
        "has_head": bool(soup.head),
        "title": soup.title.string if soup.title else None
    }

async def close_soup(soup_id: str) -> str:
    """Free memory."""
    return SoupManager.close_soup(soup_id)
