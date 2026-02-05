from mcp_servers.bs4_server.soup_manager import SoupManager
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
import difflib

async def diff_text(selector: str, other_html: str, soup_id: Optional[str] = None) -> str:
    """
    Compare text content of matching element vs other_html text.
    Returns unified diff string.
    """
    soup = SoupManager.get_soup(soup_id)
    el = soup.select_one(selector)
    text1 = el.get_text(strip=True, separator="\n").splitlines() if el else []
    
    soup2 = BeautifulSoup(other_html, "html.parser")
    # If other_html is full doc, we might want to select same selector? 
    # Or assume other_html IS the snippet. Let's assume it IS the snippet.
    text2 = soup2.get_text(strip=True, separator="\n").splitlines()
    
    diff = difflib.unified_diff(text1, text2, fromfile="Current", tofile="New", lineterm="")
    return "\n".join(diff)

async def diff_attributes(selector: str, other_html: str, soup_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Compare attributes of element vs other element.
    """
    soup = SoupManager.get_soup(soup_id)
    el1 = soup.select_one(selector)
    attrs1 = el1.attrs if el1 else {}
    
    soup2 = BeautifulSoup(other_html, "html.parser")
    # Try to find root element of other_html
    el2 = soup2.find(True)
    attrs2 = el2.attrs if el2 else {}
    
    # Calculate diff
    keys = set(attrs1.keys()) | set(attrs2.keys())
    diff = {}
    for k in keys:
        v1 = attrs1.get(k)
        v2 = attrs2.get(k)
        if v1 != v2:
            diff[k] = {"current": v1, "new": v2}
            
    return diff
