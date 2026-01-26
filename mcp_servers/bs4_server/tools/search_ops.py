from mcp_servers.bs4_server.soup_manager import SoupManager
from typing import Dict, Any, Optional, List
import re

async def find_tag(name: str, attrs: Dict[str, Any] = {}, soup_id: Optional[str] = None) -> str:
    """Find first tag matching name and attributes."""
    soup = SoupManager.get_soup(soup_id)
    tag = soup.find(name, attrs=attrs)
    return str(tag) if tag else None

async def find_all_tags(name: str, attrs: Dict[str, Any] = {}, limit: int = 0, soup_id: Optional[str] = None) -> List[str]:
    """Find all tags matching name and attributes."""
    soup = SoupManager.get_soup(soup_id)
    limit_val = limit if limit > 0 else None
    tags = soup.find_all(name, attrs=attrs, limit=limit_val)
    return [str(t) for t in tags]

async def select_one(selector: str, soup_id: Optional[str] = None) -> str:
    """Find first element matching CSS selector."""
    soup = SoupManager.get_soup(soup_id)
    tag = soup.select_one(selector)
    return str(tag) if tag else None

async def select_all(selector: str, limit: int = 0, soup_id: Optional[str] = None) -> List[str]:
    """Find all elements matching CSS selector."""
    soup = SoupManager.get_soup(soup_id)
    limit_val = limit if limit > 0 else None
    tags = soup.select(selector, limit=limit_val)
    return [str(t) for t in tags]

async def find_by_text(text_regex: str, soup_id: Optional[str] = None) -> List[str]:
    """Find elements containing text matching regex."""
    soup = SoupManager.get_soup(soup_id)
    # Using lambda to find tags that contain the text
    matcher = re.compile(text_regex)
    found = soup.find_all(string=matcher)
    # Return parent tags of the text nodes
    return list(set([str(t.parent) for t in found if t.parent]))

async def find_by_id(element_id: str, soup_id: Optional[str] = None) -> str:
    """Get element by ID."""
    soup = SoupManager.get_soup(soup_id)
    tag = soup.find(id=element_id)
    return str(tag) if tag else None

async def find_by_class(class_name: str, soup_id: Optional[str] = None) -> List[str]:
    """Get elements by Class."""
    soup = SoupManager.get_soup(soup_id)
    tags = soup.find_all(class_=class_name)
    return [str(t) for t in tags]
