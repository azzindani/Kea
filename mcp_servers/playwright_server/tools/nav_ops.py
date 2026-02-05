from mcp_servers.playwright_server.session_manager import BrowserSession
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from typing import Optional, Dict, Any, List

async def goto_page(url: str, timeout: int = 30000, wait_until: str = "domcontentloaded") -> str:
    """
    Navigate to a URL.
    wait_until: 'domcontentloaded', 'load', 'networkidle'
    """
    page = await BrowserSession.get_page()
    try:
        await page.goto(url, timeout=timeout, wait_until=wait_until)
        return f"Navigated to {url}"
    except PlaywrightTimeoutError:
        return f"Navigation timed out after {timeout}ms"
    except Exception as e:
        return f"Navigation failed: {str(e)}"

async def go_back() -> str:
    """Navigate back in history."""
    page = await BrowserSession.get_page()
    await page.go_back()
    return "Navigated back"

async def go_forward() -> str:
    """Navigate forward in history."""
    page = await BrowserSession.get_page()
    await page.go_forward()
    return "Navigated forward"

async def reload_page() -> str:
    """Reload the current page."""
    page = await BrowserSession.get_page()
    await page.reload()
    return "Page reloaded"

async def create_tab() -> str:
    """Open a new tab."""
    await BrowserSession.new_page()
    return "New tab opened"

async def close_tab() -> str:
    """Close the current tab. If it's the last one, it might close context."""
    page = await BrowserSession.get_page()
    if not page.is_closed():
        await page.close()
    return "Tab closed"

async def set_viewport(width: int, height: int) -> str:
    """Set the viewport size."""
    page = await BrowserSession.get_page()
    await page.set_viewport_size({"width": width, "height": height})
    return f"Viewport set to {width}x{height}"

async def get_current_url() -> str:
    """Get the current URL."""
    page = await BrowserSession.get_page()
    return page.url

async def get_page_title() -> str:
    """Get the page title."""
    page = await BrowserSession.get_page()
    return await page.title()
