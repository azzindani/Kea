from mcp_servers.bs4_server.soup_manager import SoupManager
from typing import Optional, List

async def strip_attributes(selector: str, attrs: List[str] = ["style", "class", "onclick", "onmouseover", "width", "height"], soup_id: Optional[str] = None) -> str:
    """
    Remove specific attributes from matching elements (or all elements in selector).
    """
    soup = SoupManager.get_soup(soup_id)
    elements = soup.select(selector)
    count = 0
    for el in elements:
        # Also traverse descendants if selector selected a container? 
        # Usually selector selects specific elements. 
        # If user wants to strip attrs from ALL descendants of a div, they should use "div *"
        for attr in attrs:
            if el.has_attr(attr):
                del el[attr]
                count += 1
    return f"Removed {count} attributes from {len(elements)} elements"

async def strip_all_attributes(selector: str = "body *", soup_id: Optional[str] = None) -> str:
    """Remove ALL attributes from elements matching selector."""
    soup = SoupManager.get_soup(soup_id)
    elements = soup.select(selector)
    for el in elements:
        el.attrs = {}
    return f"Stripped all attributes from {len(elements)} elements"

async def allowlist_tags(keep_tags: List[str] = ["p", "h1", "h2", "h3", "b", "i", "a", "ul", "li"], selector: str = "body", soup_id: Optional[str] = None) -> str:
    """
    Destructive cleaning: Remove any tag NOT in the keep list, inside the selector.
    Unwraps the forbidden tags (keeps text) or decomposes them?
    Standard sanitization usually unwraps simple formatting tags and decomposes dangerous ones (script).
    Here we will UNWRAP forbidden tags to preserve text content, unless it's script/style which we decompose.
    """
    soup = SoupManager.get_soup(soup_id)
    root = soup.select_one(selector)
    if not root:
        return "Selector not found"
        
    dangerous = ["script", "style", "iframe", "noscript", "object", "embed"]
    
    # Iterating safe approach: find all tags, check if allowed
    # Note: modifying tree while iterating requires care.
    all_tags = root.find_all(True)
    count_unwrapped = 0
    count_decomposed = 0
    
    for tag in all_tags:
        if tag.name in keep_tags:
            continue
            
        if tag.name in dangerous:
            tag.decompose()
            count_decomposed += 1
        else:
            tag.unwrap()
            count_unwrapped += 1
            
    return f"Sanitized: Kept {keep_tags}. Unwrapped {count_unwrapped}, Decomposed {count_decomposed}."
