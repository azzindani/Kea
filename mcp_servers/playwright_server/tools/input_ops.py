from mcp_servers.playwright_server.session_manager import BrowserSession
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from typing import Optional, Dict, Any, List

async def click_element(selector: str, timeout: int = 5000) -> str:
    """Click an element matching the selector."""
    page = await BrowserSession.get_page()
    try:
        await page.click(selector, timeout=timeout)
        return f"Clicked element: {selector}"
    except Exception as e:
        return f"Failed to click {selector}: {str(e)}"

async def type_text(selector: str, text: str, delay: int = 0, timeout: int = 5000) -> str:
    """Type text into an element. delay in ms between key presses."""
    page = await BrowserSession.get_page()
    try:
        await page.type(selector, text, delay=delay, timeout=timeout)
        return f"Typed '{text}' into {selector}"
    except Exception as e:
        return f"Failed to type into {selector}: {str(e)}"

async def fill_input(selector: str, value: str, timeout: int = 5000) -> str:
    """Fill an input field (clears it first)."""
    page = await BrowserSession.get_page()
    try:
        await page.fill(selector, value, timeout=timeout)
        return f"Filled {selector} with '{value}'"
    except Exception as e:
        return f"Failed to fill {selector}: {str(e)}"

async def press_key(key: str) -> str:
    """Press a key (e.g. 'Enter', 'Tab', 'Control+A')."""
    page = await BrowserSession.get_page()
    await page.keyboard.press(key)
    return f"Pressed key: {key}"

async def hover_element(selector: str, timeout: int = 5000) -> str:
    """Hover over an element."""
    page = await BrowserSession.get_page()
    try:
        await page.hover(selector, timeout=timeout)
        return f"Hovered over {selector}"
    except Exception as e:
        return f"Failed to hover {selector}: {str(e)}"

async def check_checkbox(selector: str, checked: bool = True, timeout: int = 5000) -> str:
    """Check or uncheck a checkbox."""
    page = await BrowserSession.get_page()
    try:
        if checked:
            await page.check(selector, timeout=timeout)
            return f"Checked {selector}"
        else:
            await page.uncheck(selector, timeout=timeout)
            return f"Unchecked {selector}"
    except Exception as e:
        return f"Failed to check/uncheck {selector}: {str(e)}"

async def select_option(selector: str, value: str, timeout: int = 5000) -> str:
    """Select an option in a dropdown by value."""
    page = await BrowserSession.get_page()
    try:
        await page.select_option(selector, value, timeout=timeout)
        return f"Selected '{value}' in {selector}"
    except Exception as e:
        return f"Failed to select option in {selector}: {str(e)}"

async def drag_and_drop(source: str, target: str, timeout: int = 5000) -> str:
    """Drag source element to target element."""
    page = await BrowserSession.get_page()
    try:
        await page.drag_and_drop(source, target, timeout=timeout)
        return f"Dragged {source} to {target}"
    except Exception as e:
        return f"Failed to drag and drop: {str(e)}"
