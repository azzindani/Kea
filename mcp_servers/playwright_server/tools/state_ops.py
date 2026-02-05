from mcp_servers.playwright_server.session_manager import BrowserSession
from typing import Optional, Dict, Any, List

async def get_cookies() -> List[Dict[str, Any]]:
    """Get all cookies for the current context."""
    context = await BrowserSession.get_context()
    return await context.cookies()

async def set_cookies(cookies: List[Dict[str, Any]]) -> str:
    """Set cookies. Each cookie dict must have 'name', 'value', 'url' or 'domain'."""
    context = await BrowserSession.get_context()
    await context.add_cookies(cookies)
    return f"Added {len(cookies)} cookies"

async def clear_cookies() -> str:
    """Clear all cookies."""
    context = await BrowserSession.get_context()
    await context.clear_cookies()
    return "Cookies cleared"

async def get_local_storage(key: str) -> str:
    """Get item from LocalStorage."""
    page = await BrowserSession.get_page()
    return await page.evaluate(f"localStorage.getItem('{key}')")

async def set_local_storage(key: str, value: str) -> str:
    """Set item in LocalStorage."""
    page = await BrowserSession.get_page()
    await page.evaluate(f"localStorage.setItem('{key}', '{value}')")
    return f"Set LocalStorage {key}"

async def clear_local_storage() -> str:
    """Clear LocalStorage."""
    page = await BrowserSession.get_page()
    await page.evaluate("localStorage.clear()")
    return "LocalStorage cleared"

async def get_session_storage(key: str) -> str:
    """Get item from SessionStorage."""
    page = await BrowserSession.get_page()
    return await page.evaluate(f"sessionStorage.getItem('{key}')")
