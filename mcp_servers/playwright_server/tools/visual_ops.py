from mcp_servers.playwright_server.session_manager import BrowserSession
from playwright.async_api import Page, Locator
from typing import Optional, List, Dict, Any

async def print_to_pdf(path: str, format: str = "A4", landscape: bool = False, print_background: bool = True) -> str:
    """
    Generate a PDF of the current page.
    format: 'Letter', 'Legal', 'Tabloid', 'A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6'
    """
    page = await BrowserSession.get_page()
    try:
        await page.pdf(path=path, format=format, landscape=landscape, print_background=print_background)
        return f"PDF saved to {path}"
    except Exception as e:
        return f"Error creating PDF: {str(e)}"

async def screenshot_mask(path: str, mask_selector: str, full_page: bool = True) -> str:
    """
    Take a screenshot with specific elements masked (covered).
    Useful for hiding sensitive data or dynamic ads.
    """
    page = await BrowserSession.get_page()
    try:
        mask = page.locator(mask_selector)
        # Note: mask argument accepts list of locators
        await page.screenshot(path=path, full_page=full_page, mask=[mask])
        return f"Masked screenshot saved to {path}"
    except Exception as e:
        return f"Error taking masked screenshot: {str(e)}"
