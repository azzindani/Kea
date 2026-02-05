from mcp_servers.playwright_server.session_manager import BrowserSession
from typing import Optional, Any, Union

async def wait_for_selector(selector: str, state: str = "visible", timeout: int = 30000) -> str:
    """
    Wait for element to reach state.
    state: 'attached', 'detached', 'visible', 'hidden'
    """
    page = await BrowserSession.get_page()
    try:
        await page.wait_for_selector(selector, state=state, timeout=timeout)
        return f"Waited for '{selector}' to be {state}"
    except Exception as e:
        return f"Timeout waiting for {selector}: {str(e)}"

async def wait_for_url(url_regex: str, timeout: int = 30000) -> str:
    """Wait for URL to match regex."""
    page = await BrowserSession.get_page()
    import re
    try:
        # Playwright accepts regex object or compiled pattern
        # We pass string which converts to regex or glob
        await page.wait_for_url(re.compile(url_regex), timeout=timeout)
        return f"URL matched {url_regex}"
    except Exception as e:
        return f"Timeout waiting for URL {url_regex}: {str(e)}"

async def wait_for_function(function_body: str, arg: Any = None, timeout: int = 30000) -> str:
    """
    Wait for JS function to return true.
    function_body: e.g. "() => window.scrollY > 100"
    """
    page = await BrowserSession.get_page()
    try:
        await page.wait_for_function(function_body, arg=arg, timeout=timeout)
        return "Condition met"
    except Exception as e:
        return f"Timeout waiting for function: {str(e)}"

async def explicit_wait(milliseconds: int) -> str:
    """Explicit hard wait/sleep."""
    import asyncio
    await asyncio.sleep(milliseconds / 1000)
    return f"Waited {milliseconds}ms"
