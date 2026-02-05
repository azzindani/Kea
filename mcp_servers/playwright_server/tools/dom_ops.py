from mcp_servers.playwright_server.session_manager import BrowserSession
from playwright.async_api import Page, Locator
from typing import Optional, Dict, Any, List, Union
import json

async def get_page_content() -> str:
    """Get the full HTML content of the page."""
    page = await BrowserSession.get_page()
    return await page.content()

async def get_element_text(selector: str, timeout: int = 5000) -> str:
    """Get text content of a single element."""
    page = await BrowserSession.get_page()
    try:
        # waits for element to be attached and visible
        content = await page.text_content(selector, timeout=timeout)
        return content or ""
    except Exception as e:
        return f"Error getting text for {selector}: {str(e)}"

async def get_all_text(selector: str) -> List[str]:
    """
    BULK: Get text content of ALL elements matching the selector.
    Useful for extracting lists, menu items, table rows etc.
    """
    page = await BrowserSession.get_page()
    try:
        # Locator.all_text_contents() does not wait for element to be visible, 
        # but waits for specific selector to be present if we use page.locator()
        # To be safe, let's wait for at least one
        try:
            await page.wait_for_selector(selector, timeout=2000)
        except:
             pass # proceed anyway, maybe none exist
             
        return await page.locator(selector).all_text_contents()
    except Exception as e:
        return [f"Error: {str(e)}"]

async def get_element_attribute(selector: str, attribute: str) -> str:
    """Get value of an attribute for a single element."""
    page = await BrowserSession.get_page()
    try:
        return await page.get_attribute(selector, attribute) or ""
    except Exception as e:
        return f"Error: {str(e)}"

async def get_all_attributes(selector: str, attribute: str) -> List[str]:
    """
    BULK: Get specific attribute from ALL matching elements.
    Great for extracting all links (href) or images (src).
    """
    page = await BrowserSession.get_page()
    try:
        count = await page.locator(selector).count()
        results = []
        for i in range(count):
            # nth is 0-based
            val = await page.locator(selector).nth(i).get_attribute(attribute)
            results.append(val or "")
        return results
    except Exception as e:
        return [f"Error: {str(e)}"]

async def count_elements(selector: str) -> int:
    """Count number of elements matching selector."""
    page = await BrowserSession.get_page()
    return await page.locator(selector).count()

async def evaluate_js(script: str, arg: Any = None) -> Any:
    """Execute JavaScript on the page."""
    page = await BrowserSession.get_page()
    return await page.evaluate(script, arg)

async def get_table_data(selector: str) -> List[Dict[str, str]]:
    """
    BULK: Extract data from an HTML table into a list of dictionaries.
    Assumes standard <table><thead><th>...<tbody><tr><td> structure.
    """
    page = await BrowserSession.get_page()
    try:
        # We execute JS in browser context for robust parsing
        data = await page.evaluate("""(sel) => {
            const table = document.querySelector(sel);
            if (!table) return null;
            
            const headers = Array.from(table.querySelectorAll('th')).map(th => th.innerText.trim());
            const rows = Array.from(table.querySelectorAll('tbody tr'));
            
            return rows.map(tr => {
                const cells = Array.from(tr.querySelectorAll('td'));
                const rowData = {};
                cells.forEach((td, index) => {
                    const key = headers[index] || `col_${index}`;
                    rowData[key] = td.innerText.trim();
                });
                return rowData;
            });
        }""", selector)
        
        if data is None:
            return [{"error": "Table not found"}]
        return data
    except Exception as e:
        return [{"error": str(e)}]

async def screenshot_element(selector: str, path: str) -> str:
    """Take a screenshot of a specific element."""
    page = await BrowserSession.get_page()
    try:
        await page.locator(selector).screenshot(path=path)
        return f"Screenshot of {selector} saved to {path}"
    except Exception as e:
        return f"Error: {str(e)}"

async def screenshot_page(path: str, full_page: bool = True) -> str:
    """Take a screenshot of the entire page."""
    page = await BrowserSession.get_page()
    try:
        await page.screenshot(path=path, full_page=full_page)
        return f"Page screenshot saved to {path}"
    except Exception as e:
        return f"Error: {str(e)}"
