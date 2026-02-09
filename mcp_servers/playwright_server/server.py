
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "mcp",
#   "playwright",
#   "structlog",
# ]
# ///

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from shared.mcp.fastmcp import FastMCP
from session_manager import BrowserSession
from mcp_servers.playwright_server.tools import (
    nav_ops, input_ops, dom_ops, network_ops, state_ops, chain_ops, scraper_ops,
    frame_ops, dialog_ops, device_ops, extract_ops,
    audit_ops, perf_ops, mock_ops, context_ops, clipboard_ops,
    visual_ops, gesture_ops, wait_ops, assert_ops, browser_ops
)
import structlog
import asyncio
from typing import List, Dict, Any, Optional, Union

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging import setup_logging
setup_logging()

mcp = FastMCP("playwright_server", dependencies=["playwright"])

@mcp.tool()
async def install_playwright() -> str:
    """INSTALLS Playwright browsers. [ACTION]
    
    [RAG Context]
    Chromium, Firefox, Webkit.
    """
    import subprocess
    try:
        process = await asyncio.create_subprocess_shell("playwright install chromium firefox webkit", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await process.communicate()
        return "Installed Browsers."
    except Exception as e:
        return str(e)

# ==========================================
# 1. Navigation
# ==========================================
@mcp.tool()
async def goto_page(url: str, timeout: int = 30000, wait_until: str = "domcontentloaded") -> str: 
    """NAVIGATES to URL. [ACTION]
    
    [RAG Context]
    """
    return await nav_ops.goto_page(url, timeout, wait_until)

@mcp.tool()
async def go_back() -> str: 
    """NAVIGATES back. [ACTION]
    
    [RAG Context]
    """
    return await nav_ops.go_back()

@mcp.tool()
async def go_forward() -> str: 
    """NAVIGATES forward. [ACTION]
    
    [RAG Context]
    """
    return await nav_ops.go_forward()

@mcp.tool()
async def reload_page() -> str: 
    """RELOADS current page. [ACTION]
    
    [RAG Context]
    """
    return await nav_ops.reload_page()

@mcp.tool()
async def create_tab() -> str: 
    """OPENS new tab. [ACTION]
    
    [RAG Context]
    """
    return await nav_ops.create_tab()

@mcp.tool()
async def close_tab() -> str: 
    """CLOSES current tab. [ACTION]
    
    [RAG Context]
    """
    return await nav_ops.close_tab()

@mcp.tool()
async def set_viewport(width: int, height: int) -> str: 
    """RESIZES browser window. [ACTION]
    
    [RAG Context]
    """
    return await nav_ops.set_viewport(width, height)

@mcp.tool()
async def get_url() -> str: 
    """GETS current URL. [DATA]
    
    [RAG Context]
    """
    return await nav_ops.get_current_url()

# ==========================================
# 2. Input
# ==========================================
@mcp.tool()
async def click_element(selector: str, timeout: int = 5000) -> str: 
    """CLICKS element. [ACTION]
    
    [RAG Context]
    """
    return await input_ops.click_element(selector, timeout)

@mcp.tool()
async def type_text(selector: str, text: str, delay: int = 0) -> str: 
    """TYPES text into element. [ACTION]
    
    [RAG Context]
    Types char by char.
    """
    return await input_ops.type_text(selector, text, delay)

@mcp.tool()
async def fill_input(selector: str, value: str) -> str: 
    """FILLS input field. [ACTION]
    
    [RAG Context]
    Fast fill.
    """
    return await input_ops.fill_input(selector, value)

@mcp.tool()
async def press_key(key: str) -> str: 
    """PRESSES keyboard key. [ACTION]
    
    [RAG Context]
    Enter, Tab, Escape, etc.
    """
    return await input_ops.press_key(key)

@mcp.tool()
async def hover_element(selector: str) -> str: 
    """HOVERS over element. [ACTION]
    
    [RAG Context]
    """
    return await input_ops.hover_element(selector)

@mcp.tool()
async def check_checkbox(selector: str, checked: bool = True) -> str: 
    """CHECKS/UNCHECKS checkbox. [ACTION]
    
    [RAG Context]
    """
    return await input_ops.check_checkbox(selector, checked)

@mcp.tool()
async def select_option(selector: str, value: str) -> str: 
    """SELECTS dropdown option. [ACTION]
    
    [RAG Context]
    """
    return await input_ops.select_option(selector, value)

@mcp.tool()
async def drag_and_drop(source: str, target: str) -> str: 
    """DRAGS element to target. [ACTION]
    
    [RAG Context]
    """
    return await input_ops.drag_and_drop(source, target)

# ==========================================
# 3. DOM & Extraction
# ==========================================
# ==========================================
# 3. DOM & Extraction
# ==========================================
@mcp.tool()
async def get_page_content() -> str: 
    """GETS full page HTML. [DATA]
    
    [RAG Context]
    """
    return await dom_ops.get_page_content()

@mcp.tool()
async def get_element_text(selector: str) -> str: 
    """GETS element text. [DATA]
    
    [RAG Context]
    """
    return await dom_ops.get_element_text(selector)

@mcp.tool()
async def get_all_text(selector: str) -> List[str]: 
    """GETS text from all matching elements. [DATA]
    
    [RAG Context]
    """
    return await dom_ops.get_all_text(selector)

@mcp.tool()
async def get_attribute(selector: str, attribute: str) -> str: 
    """GETS element attribute. [DATA]
    
    [RAG Context]
    """
    return await dom_ops.get_element_attribute(selector, attribute)

@mcp.tool()
async def get_all_attributes(selector: str, attribute: str) -> List[str]: 
    """GETS attributes from all matching elements. [DATA]
    
    [RAG Context]
    """
    return await dom_ops.get_all_attributes(selector, attribute)

@mcp.tool()
async def get_table_data(selector: str) -> List[Dict[str, str]]: 
    """EXTRACTS table data. [DATA]
    
    [RAG Context]
    Returns list of dicts (row headers).
    """
    return await dom_ops.get_table_data(selector)

@mcp.tool()
async def evaluate_js(script: str, arg: Any = None) -> Any: 
    """EXECUTES JavaScript. [ACTION]
    
    [RAG Context]
    Runs within page context.
    """
    return await dom_ops.evaluate_js(script, arg)

@mcp.tool()
async def screenshot(selector: str, path: str) -> str: 
    """CAPTURES element screenshot. [DATA]
    
    [RAG Context]
    """
    return await dom_ops.screenshot_element(selector, path)

@mcp.tool()
async def screenshot_page(path: str) -> str: 
    """CAPTURES page screenshot. [DATA]
    
    [RAG Context]
    """
    return await dom_ops.screenshot_page(path)

# ==========================================
# 4. Network & State
# ==========================================
@mcp.tool()
async def block_resources(resource_types: List[str] = ["image", "stylesheet", "font"]) -> str: 
    """BLOCKS images/css/fonts. [ACTION]
    
    [RAG Context]
    Speeds up scraping.
    """
    return await network_ops.block_resources(resource_types)

@mcp.tool()
async def get_cookies() -> List[Dict[str, Any]]: 
    """GETS cookies. [DATA]
    
    [RAG Context]
    """
    return await state_ops.get_cookies()

@mcp.tool()
async def set_cookies(cookies: List[Dict[str, Any]]) -> str: 
    """SETS cookies. [ACTION]
    
    [RAG Context]
    """
    return await state_ops.set_cookies(cookies)

@mcp.tool()
async def clear_cookies() -> str: 
    """CLEARS cookies. [ACTION]
    
    [RAG Context]
    """
    return await state_ops.clear_cookies()

# ==========================================
# 5. Frames & Dialogs
# ==========================================
# ==========================================
# 5. Frames & Dialogs
# ==========================================
@mcp.tool()
async def frame_click(selector: str, frame_name: Optional[str] = None) -> str: 
    """CLICKS element in frame. [ACTION]
    
    [RAG Context]
    """
    return await frame_ops.frame_click(selector, frame_name)

@mcp.tool()
async def frame_fill(selector: str, value: str, frame_name: Optional[str] = None) -> str: 
    """FILLS input in frame. [ACTION]
    
    [RAG Context]
    """
    return await frame_ops.frame_fill(selector, value, frame_name)

@mcp.tool()
async def handle_dialog(action: str = "accept", prompt_text: Optional[str] = None) -> str: 
    """HANDLES alerts/prompts. [ACTION]
    
    [RAG Context]
    """
    return await dialog_ops.handle_dialog(action, prompt_text)

@mcp.tool()
async def enable_console() -> str: 
    """CAPTURES console logs. [ACTION]
    
    [RAG Context]
    """
    return await dialog_ops.enable_console_capture()

@mcp.tool()
async def get_console() -> List[str]: 
    """GETS captured logs. [DATA]
    
    [RAG Context]
    """
    return await dialog_ops.get_console_logs()

# ==========================================
# 6. Device & Deep Extract
# ==========================================
@mcp.tool()
async def set_geolocation(latitude: float, longitude: float) -> str: 
    """SETS fake location. [ACTION]
    
    [RAG Context]
    """
    return await device_ops.set_geolocation(latitude, longitude)

@mcp.tool()
async def grant_permissions(permissions: List[str]) -> str: 
    """GRANTS permissions. [ACTION]
    
    [RAG Context]
    """
    return await device_ops.grant_permissions(permissions)

@mcp.tool()
async def extract_links(selector: str = "a", match_pattern: Optional[str] = None) -> List[str]: 
    """EXTRACTS all links. [DATA]
    
    [RAG Context]
    """
    return await extract_ops.extract_links(selector, match_pattern)

@mcp.tool()
async def get_computed_style(selector: str, property: str) -> str: 
    """GETS CSS style. [DATA]
    
    [RAG Context]
    """
    return await extract_ops.get_computed_style(selector, property)

# ==========================================
# 7. Audit & Perf
# ==========================================
# ==========================================
# 7. Audit & Perf
# ==========================================
@mcp.tool()
async def audit_accessibility(selector: str = "body") -> Dict[str, Any]: 
    """CHECKS accessibility (A11y). [DATA]
    
    [RAG Context]
    Uses Axe-core.
    """
    return await audit_ops.check_accessibility(selector)

@mcp.tool()
async def audit_seo() -> Dict[str, Any]: 
    """CHECKS SEO basics. [DATA]
    
    [RAG Context]
    """
    return await audit_ops.audit_seo()

@mcp.tool()
async def get_performance() -> Dict[str, float]: 
    """GETS performance metrics. [DATA]
    
    [RAG Context]
    Navigation timing, etc.
    """
    return await perf_ops.get_performance_metrics()

@mcp.tool()
async def start_tracing(path: str = "trace.zip") -> str: 
    """STARTS trace recording. [ACTION]
    
    [RAG Context]
    Debugging tool.
    """
    return await perf_ops.start_tracing(path)

@mcp.tool()
async def stop_tracing(path: str = "trace.zip") -> str: 
    """STOPS trace recording. [ACTION]
    
    [RAG Context]
    """
    return await perf_ops.stop_tracing(path)

# ==========================================
# 8. Mocking & Context
# ==========================================
@mcp.tool()
async def mock_api(url_pattern: str, body: Dict[str, Any]) -> str: 
    """MOCKS API response. [ACTION]
    
    [RAG Context]
    Intersects requests.
    """
    return await mock_ops.mock_api_response(url_pattern, body)

@mcp.tool()
async def abort_requests(url_pattern: str) -> str: 
    """ABORTS network requests. [ACTION]
    
    [RAG Context]
    """
    return await mock_ops.route_abort(url_pattern)

@mcp.tool()
async def save_session(path: str) -> str: 
    """SAVES browser state/storage. [ACTION]
    
    [RAG Context]
    """
    return await context_ops.save_storage_state(path)

@mcp.tool()
async def load_session(path: str) -> str: 
    """LOADS browser state/storage. [ACTION]
    
    [RAG Context]
    Restores cookies/localStorage.
    """
    return await context_ops.load_storage_state(path)

@mcp.tool()
async def get_clipboard() -> str: 
    """READS clipboard. [DATA]
    
    [RAG Context]
    """
    return await clipboard_ops.read_clipboard()

@mcp.tool()
async def set_clipboard(text: str) -> str: 
    """WRITES to clipboard. [ACTION]
    
    [RAG Context]
    """
    return await clipboard_ops.write_clipboard(text)

# ==========================================
# 9. Visual & Gesture (Hyper)
# ==========================================
# ==========================================
# 9. Visual & Gesture (Hyper)
# ==========================================
@mcp.tool()
async def print_to_pdf(path: str, format: str = "A4") -> str: 
    """SAVES page as PDF. [ACTION]
    
    [RAG Context]
    """
    return await visual_ops.print_to_pdf(path, format)

@mcp.tool()
async def screenshot_mask(path: str, mask_selector: str) -> str: 
    """CAPTURES screenshot with mask. [DATA]
    
    [RAG Context]
    Hides sensitive data.
    """
    return await visual_ops.screenshot_mask(path, mask_selector)

@mcp.tool()
async def tap_point(x: float, y: float) -> str: 
    """TAPS coordinates. [ACTION]
    
    [RAG Context]
    Mobile emulation.
    """
    return await gesture_ops.tap_point(x, y)

@mcp.tool()
async def swipe(x_start: float, y_start: float, x_end: float, y_end: float) -> str: 
    """SWIPES across screen. [ACTION]
    
    [RAG Context]
    Mobile emulation.
    """
    return await gesture_ops.swipe(x_start, y_start, x_end, y_end)

# ==========================================
# 10. Wait & Assert (Hyper)
# ==========================================
@mcp.tool()
async def wait_for_selector(selector: str, state: str = "visible", timeout: int = 30000) -> str: 
    """WAITS for element presence. [ACTION]
    
    [RAG Context]
    """
    return await wait_ops.wait_for_selector(selector, state, timeout)

@mcp.tool()
async def wait_for_url(url_regex: str, timeout: int = 30000) -> str: 
    """WAITS for URL match. [ACTION]
    
    [RAG Context]
    """
    return await wait_ops.wait_for_url(url_regex, timeout)

@mcp.tool()
async def wait_for_function(function_body: str, arg: Any = None) -> str: 
    """WAITS for JS condition. [ACTION]
    
    [RAG Context]
    """
    return await wait_ops.wait_for_function(function_body, arg)

@mcp.tool()
async def assert_title(expected: str) -> str: 
    """VERIFIES page title. [DATA]
    
    [RAG Context]
    Test assertion.
    """
    return await assert_ops.assert_title(expected)

@mcp.tool()
async def assert_text(text: str) -> str: 
    """VERIFIES text presence. [DATA]
    
    [RAG Context]
    Test assertion.
    """
    return await assert_ops.assert_text_present(text)

@mcp.tool()
async def assert_count(selector: str, min_count: int) -> str: 
    """VERIFIES element count. [DATA]
    
    [RAG Context]
    Test assertion.
    """
    return await assert_ops.assert_element_count(selector, min_count)

# ==========================================
# 11. Browser Infra (Hyper)
# ==========================================
@mcp.tool()
async def launch_browser(browser_type: str = "chromium") -> str: 
    """STARTS browser instance. [ACTION]
    
    [RAG Context]
    """
    return await browser_ops.launch_browser(browser_type)

@mcp.tool()
async def get_browser_info() -> Dict[str, str]: 
    """GETS browser metadata. [DATA]
    
    [RAG Context]
    Version, user agent.
    """
    return await browser_ops.get_browser_info()

@mcp.tool()
async def close_browser() -> str: 
    """CLOSES browser and cleans up resources. [ACTION]
    
    [RAG Context]
    """
    await BrowserSession.close()
    return "Browser closed."

# ==========================================
# 12. Super Tools
# ==========================================
@mcp.tool()
async def execute_browser_chain(steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]: 
    """EXECUTES sequence of actions. [ACTION]
    
    [RAG Context]
    Batched execution.
    """
    return await chain_ops.execute_browser_chain(steps)

@mcp.tool()
async def scrape_infinite_scroll(item_selector: str, max_scrolls: int = 10) -> str: 
    """SCRAPES infinite scroll pages. [ACTION]
    
    [RAG Context]
    Auto-scrolls and collects items.
    """
    return await scraper_ops.scrape_infinite_scroll(item_selector, max_scrolls)

@mcp.tool()
async def scrape_pagination(next_button_selector: str, item_selector: str, max_pages: int = 5) -> Dict[str, Any]: 
    """SCRAPES paginated lists. [ACTION]
    
    [RAG Context]
    Clicks 'Next' automatically.
    """
    return await scraper_ops.scrape_pagination(next_button_selector, item_selector, max_pages)


if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class PlaywrightServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []
