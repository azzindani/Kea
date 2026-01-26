from mcp_servers.bs4_server.soup_manager import SoupManager
from typing import Dict, Any, Optional, List, Union
from bs4 import Tag, NavigableString

def _serialize_element(element: Union[Tag, NavigableString]) -> Dict[str, Any]:
    """Helper to serialize a BS4 element."""
    if isinstance(element, NavigableString):
        return {"type": "text", "content": str(element).strip()[:50]}
    
    return {
        "type": "tag",
        "name": element.name,
        "classes": element.get("class", []),
        "id": element.get("id"),
        "text_preview": element.get_text(strip=True)[:50]
    }

async def get_parent(selector: str, soup_id: Optional[str] = None) -> Dict[str, Any]:
    """Get parent of the first element matching selector."""
    soup = SoupManager.get_soup(soup_id)
    el = soup.select_one(selector)
    if not el or not el.parent:
        return {"error": "Element or parent not found"}
    return _serialize_element(el.parent)

async def get_children(selector: str, soup_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get direct children of matching element."""
    soup = SoupManager.get_soup(soup_id)
    el = soup.select_one(selector)
    if not el:
        return []
    return [_serialize_element(c) for c in el.children if c.name] # Filter out empty whitespace strings if desired

async def get_siblings(selector: str, soup_id: Optional[str] = None) -> Dict[str, Any]:
    """Get next and previous siblings."""
    soup = SoupManager.get_soup(soup_id)
    el = soup.select_one(selector)
    if not el:
        return {"error": "Element not found"}
    
    return {
        "next": _serialize_element(el.find_next_sibling()) if el.find_next_sibling() else None,
        "prev": _serialize_element(el.find_previous_sibling()) if el.find_previous_sibling() else None
    }

async def get_path(selector: str, soup_id: Optional[str] = None) -> str:
    """Get CSS path to element."""
    soup = SoupManager.get_soup(soup_id)
    el = soup.select_one(selector)
    if not el:
        return "Element not found"
        
    path = []
    parent = el
    while parent and parent.name != '[document]':
        name = parent.name
        if parent.get('id'):
            name += f"#{parent.get('id')}"
        elif parent.get('class'):
            name += "." + ".".join(parent.get('class'))
        path.insert(0, name)
        parent = parent.parent
    return " > ".join(path)
