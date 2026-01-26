from mcp_servers.playwright_server.session_manager import BrowserSession
from typing import Any, Optional

async def assert_title(expected_title: str) -> str:
    """Assert page title equals exactly."""
    page = await BrowserSession.get_page()
    actual = await page.title()
    if actual == expected_title:
        return "Assertion Passed: Title matches."
    return f"Assertion Failed: Expected '{expected_title}', got '{actual}'"

async def assert_text_present(text: str) -> str:
    """Assert text exists anywhere on content."""
    page = await BrowserSession.get_page()
    content = await page.content()
    if text in content:
        return f"Assertion Passed: found '{text}'"
    return f"Assertion Failed: '{text}' not found in content"

async def assert_element_count(selector: str, min_count: int = 1) -> str:
    """Assert at least min_count elements exist."""
    page = await BrowserSession.get_page()
    count = await page.locator(selector).count()
    if count >= min_count:
        return f"Assertion Passed: Found {count} elements (required >= {min_count})"
    return f"Assertion Failed: Found {count} elements (expected >= {min_count})"

async def assert_element_visible(selector: str) -> str:
    """Assert element is visible."""
    page = await BrowserSession.get_page()
    if await page.locator(selector).first.is_visible():
        return f"Assertion Passed: {selector} is visible"
    return f"Assertion Failed: {selector} is hidden/missing"
