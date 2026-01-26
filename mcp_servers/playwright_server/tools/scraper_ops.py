from mcp_servers.playwright_server.session_manager import BrowserSession
from mcp_servers.playwright_server.tools import dom_ops
import asyncio
from typing import Optional, Dict, Any, List

async def scrape_infinite_scroll(scroll_container_selector: Optional[str] = None, item_selector: str = "div.item", max_scrolls: int = 10, delay: int = 1000) -> str:
    """
    Scroll down the page/element until no new items appear or max_scrolls reached.
    If scroll_container_selector is None, scrolls window.
    """
    page = await BrowserSession.get_page()
    last_count = await page.locator(item_selector).count()
    
    for i in range(max_scrolls):
        # Scroll
        if scroll_container_selector:
             await page.evaluate(f"document.querySelector('{scroll_container_selector}').scrollTop += 1000")
        else:
             await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
             
        await asyncio.sleep(delay / 1000)
        
        new_count = await page.locator(item_selector).count()
        if new_count == last_count:
            # Try once more just in case
            await asyncio.sleep(1)
            new_count = await page.locator(item_selector).count()
            if new_count == last_count:
                break # Stabilized
                
        last_count = new_count
        
    return f"Scrolled {i+1} times. Found {last_count} items matching {item_selector}"

async def scrape_pagination(next_button_selector: str, item_selector: str, max_pages: int = 5) -> Dict[str, Any]:
    """
    Click 'Next' button and collect item tokens/text until limit.
    Warning: This is a complex logic, simplifying for RPC.
    Returns: {"total_pages": n, "all_items": [list of lists]}
    """
    page = await BrowserSession.get_page()
    all_data = []
    
    for i in range(max_pages):
        # Collect data from current page
        items = await dom_ops.get_all_text(item_selector)
        all_data.append(items)
        
        # Check next button
        if await page.locator(next_button_selector).is_visible():
            await page.click(next_button_selector)
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(1) # Extra stability
        else:
            break
            
    return {
        "pages_scraped": len(all_data),
        "total_items": sum(len(x) for x in all_data),
        "data": all_data
    }
