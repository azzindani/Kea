from mcp_servers.bs4_server.soup_manager import SoupManager
from typing import Dict, Any, Optional, List, Union
import json

async def bulk_extract_css(selector_map: Dict[str, str], scope_selector: Optional[str] = None, soup_id: Optional[str] = None) -> Any:
    """
    Extract multiple fields at once using a dictionary of CSS selectors.
    selector_map: {"title": "h1", "price": ".price"}
    scope_selector: If provided, find ALL elements matching scope, then extract map from EACH. (List of Dicts)
    If no scope, extract map from root (Single Dict).
    """
    soup = SoupManager.get_soup(soup_id)
    
    if scope_selector:
        # List of objects
        results = []
        items = soup.select(scope_selector)
        for item in items:
            obj = {}
            for key, sel in selector_map.items():
                match = item.select_one(sel)
                obj[key] = match.get_text(strip=True) if match else None
            results.append(obj)
        return results
    else:
        # Single object
        obj = {}
        for key, sel in selector_map.items():
            match = soup.select_one(sel)
            obj[key] = match.get_text(strip=True) if match else None
        return obj

async def clean_html_structure(remove_tags: List[str] = ["script", "style", "iframe", "noscript", "meta"], start_soup_id: Optional[str] = None) -> str:
    """
    Remove specified tags to clean up the HTML structure.
    Useful before LLM processing to reduce tokens.
    """
    soup = SoupManager.get_soup(start_soup_id)
    count = 0
    for tag in remove_tags:
        found = soup.find_all(tag)
        for el in found:
            el.decompose()
            count += 1
    return f"Removed {count} tags ({', '.join(remove_tags)})"

async def extract_table_static(table_selector: str = "table", soup_id: Optional[str] = None) -> List[List[str]]:
    """
    Convert HTML table to List of Lists.
    Handles rowspans/colspans naïvely (repeats value).
    """
    soup = SoupManager.get_soup(soup_id)
    table = soup.select_one(table_selector)
    if not table:
        return []
    
    data = []
    rows = table.find_all("tr")
    for row in rows:
        cols = row.find_all(["td", "th"])
        # Simple extraction, not handling complex rowspan logic perfectly due to complexity
        row_data = [ele.get_text(strip=True) for ele in cols]
        if row_data:
            data.append(row_data)
    return data

async def html_to_structure(max_depth: int = 3, soup_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate a JSON tree of the DOM structure (tags only, no text).
    Useful for LLM to see the layout without token usage.
    """
    soup = SoupManager.get_soup(soup_id)
    root = soup.body if soup.body else soup
    
    def traverse(element, current_depth):
        if current_depth > max_depth:
            return "..."
        if not element.name:
            return None
            
        tree = {element.name: []}
        for child in element.children:
            if child.name:
                res = traverse(child, current_depth + 1)
                if res:
                    tree[element.name].append(res)
        return tree

    return traverse(root, 0)
