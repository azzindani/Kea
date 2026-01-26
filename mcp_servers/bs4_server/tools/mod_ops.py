from mcp_servers.bs4_server.soup_manager import SoupManager
from typing import Dict, Any, Optional, List, Union
from bs4 import BeautifulSoup

async def decompose_tag(selector: str, soup_id: Optional[str] = None) -> str:
    """Permanently remove matching elements."""
    soup = SoupManager.get_soup(soup_id)
    matches = soup.select(selector)
    count = len(matches)
    for tag in matches:
        tag.decompose()
    return f"Decomposed {count} elements matching '{selector}'"

async def extract_tag(selector: str, soup_id: Optional[str] = None) -> str:
    """Remove and return matching elements HTML."""
    soup = SoupManager.get_soup(soup_id)
    matches = soup.select(selector)
    extracted = [str(t.extract()) for t in matches]
    return f"Extracted {len(extracted)} elements" # Returning full HTML might be huge

async def replace_with(selector: str, new_html: str, soup_id: Optional[str] = None) -> str:
    """Replace matching elements with new HTML."""
    soup = SoupManager.get_soup(soup_id)
    matches = soup.select(selector)
    count = len(matches)
    
    # Create temp soup to parse new_html
    new_content = BeautifulSoup(new_html, "html.parser")
    
    for tag in matches:
        # We need a fresh copy for each replacement if there are multiple matches
        # otherwise we move the same element around
        import copy
        replacement = copy.copy(new_content) if count > 1 else new_content
        tag.replace_with(replacement)
        
    return f"Replaced {count} elements"

async def insert_after(selector: str, html: str, soup_id: Optional[str] = None) -> str:
    """Insert HTML after matching elements."""
    soup = SoupManager.get_soup(soup_id)
    matches = soup.select(selector)
    count = len(matches)
    
    for tag in matches:
        new_tag = BeautifulSoup(html, "html.parser")
        tag.insert_after(new_tag)
    return f"Inserted content after {count} elements"

async def insert_before(selector: str, html: str, soup_id: Optional[str] = None) -> str:
    """Insert HTML before matching elements."""
    soup = SoupManager.get_soup(soup_id)
    matches = soup.select(selector)
    count = len(matches)
    
    for tag in matches:
        new_tag = BeautifulSoup(html, "html.parser")
        tag.insert_before(new_tag)
    return f"Inserted content before {count} elements"

async def wrap_tag(selector: str, wrapper_tag: str, soup_id: Optional[str] = None) -> str:
    """Wrap matching elements in new tag (e.g. 'div')."""
    soup = SoupManager.get_soup(soup_id)
    matches = soup.select(selector)
    count = len(matches)
    
    for tag in matches:
        new_wrapper = soup.new_tag(wrapper_tag)
        tag.wrap(new_wrapper)
    return f"Wrapped {count} elements in <{wrapper_tag}>"

async def unwrap_tag(selector: str, soup_id: Optional[str] = None) -> str:
    """Remove the tag but keep its contents."""
    soup = SoupManager.get_soup(soup_id)
    matches = soup.select(selector)
    count = len(matches)
    
    for tag in matches:
        tag.unwrap()
    return f"Unwrapped {count} elements"

async def add_class(selector: str, class_name: str, soup_id: Optional[str] = None) -> str:
    """Append class to elements."""
    soup = SoupManager.get_soup(soup_id)
    matches = soup.select(selector)
    for tag in matches:
        exist = tag.get("class", [])
        if class_name not in exist:
            exist.append(class_name)
            tag["class"] = exist
    return f"Added class '{class_name}' to {len(matches)} elements"

async def remove_class(selector: str, class_name: str, soup_id: Optional[str] = None) -> str:
    """Remove class from elements."""
    soup = SoupManager.get_soup(soup_id)
    matches = soup.select(selector)
    for tag in matches:
        exist = tag.get("class", [])
        if class_name in exist:
            exist.remove(class_name)
            tag["class"] = exist
    return f"Removed class '{class_name}' from {len(matches)} elements"

async def set_attr(selector: str, attr: str, value: str, soup_id: Optional[str] = None) -> str:
    """Set attribute value."""
    soup = SoupManager.get_soup(soup_id)
    matches = soup.select(selector)
    for tag in matches:
        tag[attr] = value
    return f"Set {attr}='{value}' on {len(matches)} elements"
