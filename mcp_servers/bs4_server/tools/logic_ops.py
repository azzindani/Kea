from mcp_servers.bs4_server.soup_manager import SoupManager
from typing import Optional, List
import re

async def remove_if_contains(text_regex: str, selector: str = "div", soup_id: Optional[str] = None) -> str:
    """
    Remove elements matching selector IF they contain text matching the regex.
    Useful for removing ads like "Sponsored Content".
    """
    soup = SoupManager.get_soup(soup_id)
    candidates = soup.select(selector)
    count = 0
    pattern = re.compile(text_regex, re.IGNORECASE)
    
    for tag in candidates:
        if pattern.search(tag.get_text()):
            tag.decompose()
            count += 1
            
    return f"Removed {count} elements matching '{selector}' with text '{text_regex}'"

async def keep_if_parent(keep_selector: str, match_selector: str, soup_id: Optional[str] = None) -> str:
    """
    Keep elements matching `match_selector` ONLY IF they are descendants of `keep_selector`.
    (Actually, this might be redundant with CSS selectors like `parent matching`).
    
    Better logic tool: `isolate_element`.
    """
    # Let's implement isolate instead
    pass

async def isolate_element(selector: str,  soup_id: Optional[str] = None) -> str:
    """
    Destructive! Removes EVERYTHING except the first match of selector.
    """
    soup = SoupManager.get_soup(soup_id)
    target = soup.select_one(selector)
    if not target:
        return "Target not found"
    
    # We can replace body contents with this target or just return it as new soup?
    # Modifying state:
    if soup.body:
        soup.body.clear()
        soup.body.append(target)
    else:
        soup.clear()
        soup.append(target)
        
    return f"Isolated '{selector}'. All other content removed."
