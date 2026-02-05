from mcp_servers.playwright_server.session_manager import BrowserSession
from typing import Optional, List, Dict, Any

async def get_computed_style(selector: str, property: str) -> str:
    """Get the computed CSS value of a property."""
    page = await BrowserSession.get_page()
    # Using eval to get computed style
    return await page.evaluate(f"""
        (selector) => {{
            const el = document.querySelector(selector);
            return el ? window.getComputedStyle(el).getPropertyValue('{property}') : '';
        }}
    """, selector)

async def get_bounding_box(selector: str) -> Dict[str, float]:
    """Get element geometry (x, y, width, height)."""
    page = await BrowserSession.get_page()
    box = await page.locator(selector).bounding_box()
    return box or {}

async def extract_links(selector: str = "a", match_pattern:  Optional[str] = None) -> List[str]:
    """
    Extract all href attribute from links. 
    match_pattern: Optional regex string to filter the hrefs.
    """
    page = await BrowserSession.get_page()
    hrefs = await page.eval_on_selector_all(selector, "elements => elements.map(e => e.href)")
    
    if match_pattern:
        import re
        hrefs = [h for h in hrefs if re.search(match_pattern, h)]
        
    return hrefs

async def extract_images(selector: str = "img") -> List[str]:
    """Extract src attributes from images."""
    page = await BrowserSession.get_page()
    return await page.eval_on_selector_all(selector, "elements => elements.map(e => e.src)")

async def get_accessibility_snapshot(root_selector: Optional[str] = None) -> Dict[str, Any]:
    """Get the accessibility tree snapshot."""
    page = await BrowserSession.get_page()
    if root_selector:
        element = await page.query_selector(root_selector)
        if element:
            return await page.accessibility.snapshot(root=element)
    return await page.accessibility.snapshot()
