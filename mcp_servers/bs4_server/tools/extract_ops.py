from mcp_servers.bs4_server.soup_manager import SoupManager
from typing import Dict, Any, Optional, List, Union

async def get_text(selector: str, strip: bool = True, soup_id: Optional[str] = None) -> str:
    """Get text content of first matching element."""
    soup = SoupManager.get_soup(soup_id)
    el = soup.select_one(selector)
    return el.get_text(strip=strip) if el else None

async def get_all_text(selector: str, strip: bool = True, separator: str = "\\n", soup_id: Optional[str] = None) -> List[str]:
    """Get text matching elements."""
    soup = SoupManager.get_soup(soup_id)
    return [el.get_text(strip=strip, separator=separator) for el in soup.select(selector)]

async def get_attr(selector: str, attr: str, soup_id: Optional[str] = None) -> str:
    """Get specific attribute."""
    soup = SoupManager.get_soup(soup_id)
    el = soup.select_one(selector)
    if el and el.has_attr(attr):
        val = el[attr]
        return " ".join(val) if isinstance(val, list) else str(val)
    return None

async def get_attrs(selector: str, soup_id: Optional[str] = None) -> Dict[str, Any]:
    """Get all attributes of first match."""
    soup = SoupManager.get_soup(soup_id)
    el = soup.select_one(selector)
    return el.attrs if el else None

async def get_all_attrs(selector: str, attr: str, soup_id: Optional[str] = None) -> List[str]:
    """Get specific attribute from ALL matching elements."""
    soup = SoupManager.get_soup(soup_id)
    results = []
    for el in soup.select(selector):
        if el.has_attr(attr):
            val = el[attr]
            results.append(" ".join(val) if isinstance(val, list) else str(val))
        else:
            results.append(None)
    return results

async def get_data_attrs(selector: str, soup_id: Optional[str] = None) -> Dict[str, str]:
    """Get all data-* attributes."""
    soup = SoupManager.get_soup(soup_id)
    el = soup.select_one(selector)
    if not el:
        return {}
    return {k: v for k, v in el.attrs.items() if k.startswith("data-")}

async def get_classes(selector: str, soup_id: Optional[str] = None) -> List[str]:
    """Get list of classes."""
    soup = SoupManager.get_soup(soup_id)
    el = soup.select_one(selector)
    return el.get("class", []) if el else []

async def has_attr(selector: str, attr: str, soup_id: Optional[str] = None) -> bool:
    """Check if element has attribute."""
    soup = SoupManager.get_soup(soup_id)
    el = soup.select_one(selector)
    return el.has_attr(attr) if el else False
