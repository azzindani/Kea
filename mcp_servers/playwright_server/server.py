
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
# from mcp_servers.playwright_server.tools import (
#     nav_ops, input_ops, dom_ops, network_ops, state_ops, chain_ops, scraper_ops,
#     frame_ops, dialog_ops, device_ops, extract_ops,
#     audit_ops, perf_ops, mock_ops, context_ops, clipboard_ops,
#     visual_ops, gesture_ops, wait_ops, assert_ops, browser_ops
# )
# Note: Tools will be imported lazily inside each tool function to speed up startup.

import structlog
import asyncio
from typing import List, Dict, Any, Optional, Union

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging(force_stderr=True)

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
    Instructs the browser to navigate to a specific web address. This is the starting point for almost all browser-based tasks.
    
    How to Use:
    - Provide the full URL.
    - 'wait_until' options:
        - 'domcontentloaded': Fast, waits for HTML to load.
        - 'load': Waits for all resources (images/css).
        - 'networkidle': Waits until there's no network activity for 500ms (best for SPAs).
    
    Arguments:
    - url (str): The target website.
    - timeout (int): Max wait time in milliseconds.
    
    Keywords: visit website, open page, browser navigation, web entry.
    """
    from mcp_servers.playwright_server.tools import nav_ops
    return await nav_ops.goto_page(url, timeout, wait_until)

@mcp.tool()
async def go_back() -> str: 
    """NAVIGATES back. [ACTION]
    
    [RAG Context]
    Simulates the browser's "Back" button to return to the previously visited page in the session history.
    
    Keywords: previous page, go back, return to last, browser history back.
    """
    from mcp_servers.playwright_server.tools import nav_ops
    return await nav_ops.go_back()

@mcp.tool()
async def go_forward() -> str: 
    """NAVIGATES forward. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.playwright_server.tools import nav_ops
    return await nav_ops.go_forward()

@mcp.tool()
async def reload_page() -> str: 
    """RELOADS current page. [ACTION]
    
    [RAG Context]
    Refreshes the current active tab. Use this to ensure the most up-to-date content is loaded or to clear temporary UI glitches.
    
    Keywords: refresh page, reload tab, force update, browser refresh.
    """
    from mcp_servers.playwright_server.tools import nav_ops
    return await nav_ops.reload_page()

@mcp.tool()
async def create_tab() -> str: 
    """OPENS new tab. [ACTION]
    
    [RAG Context]
    Creates a new, empty browser tab and makes it the active target for subsequent tools.
    
    Keywords: new tab, open browser, tab context, session expansion.
    """
    from mcp_servers.playwright_server.tools import nav_ops
    return await nav_ops.create_tab()

@mcp.tool()
async def close_tab() -> str: 
    """CLOSES current tab. [ACTION]
    
    [RAG Context]
    Terminates the current active tab. 
    
    Keywords: close browser, exit tab, terminate session.
    """
    from mcp_servers.playwright_server.tools import nav_ops
    return await nav_ops.close_tab()

@mcp.tool()
async def set_viewport(width: int, height: int) -> str: 
    """RESIZES browser window. [ACTION]
    
    [RAG Context]
    Simulates a screen of specific dimensions (e.g., Mobile (360x800) vs Desktop (1920x1080)).
    
    How to Use:
    - Crucial for testing Responsive Design or bypassing anti-bot measures that check for headless-sized windows.
    
    Keywords: change resolution, window size, viewport dimensions, screen simulation.
    """
    from mcp_servers.playwright_server.tools import nav_ops
    return await nav_ops.set_viewport(width, height)

@mcp.tool()
async def get_url() -> str: 
    """GETS current URL. [DATA]
    
    [RAG Context]
    """
    from mcp_servers.playwright_server.tools import nav_ops
    return await nav_ops.get_current_url()

# ==========================================
# 2. Input
# ==========================================
@mcp.tool()
async def click_element(selector: str, timeout: int = 5000) -> str: 
    """CLICKS element. [ACTION]
    
    [RAG Context]
    Simulates a mouse click on a specific DOM element.
    
    How to Use:
    - Use CSS selectors (e.g., 'button#submit', '.login-link', 'text="Accept"').
    - The tool automatically scrolls the element into view and waits for it to become 'actionable' (visible and stable).
    
    Arguments:
    - selector (str): CSS or Playwright selector.
    
    Keywords: mouse click, button press, interact with element, submit form.
    """
    from mcp_servers.playwright_server.tools import input_ops
    return await input_ops.click_element(selector, timeout)

@mcp.tool()
async def type_text(selector: str, text: str, delay: int = 0) -> str: 
    """TYPES text into element. [ACTION]
    
    [RAG Context]
    Sends individual keystrokes to an input field, simulating human typing behavior.
    
    How to Use:
    - Use for search bars, login fields, and comment boxes.
    - Set 'delay' (ms) to make it look more human and bypass simple anti-bot scripts.
    
    Arguments:
    - selector (str): Target input field.
    - text (str): Content to type.
    - delay (int): Milliseconds between keystrokes.
    
    Keywords: human typing, input text, keyboard simulation, form filling.
    """
    from mcp_servers.playwright_server.tools import input_ops
    return await input_ops.type_text(selector, text, delay)

@mcp.tool()
async def fill_input(selector: str, value: str) -> str: 
    """FILLS input field. [ACTION]
    
    [RAG Context]
    Instantly clears the input field and enters the provided 'value' as a single block.
    
    How to Use:
    - Faster than 'type_text', but less human-like.
    - Ideal for long data entries where human simulation is not required.
    
    Keywords: input value, set text, fast input, data entry.
    """
    from mcp_servers.playwright_server.tools import input_ops
    return await input_ops.fill_input(selector, value)

@mcp.tool()
async def press_key(key: str) -> str: 
    """PRESSES keyboard key. [ACTION]
    
    [RAG Context]
    Sends a single key press event to the browser.
    
    How to Use:
    - Supports named keys like 'Enter', 'Escape', 'Tab', 'ArrowUp', 'PageDown'.
    - Can also accept modifier key combinations like 'Control+C' or 'Meta+A'.
    
    Keywords: keyboard shortcut, hotkey, enter key, tab navigation.
    """
    from mcp_servers.playwright_server.tools import input_ops
    return await input_ops.press_key(key)

@mcp.tool()
async def hover_element(selector: str) -> str: 
    """HOVERS over element. [ACTION]
    
    [RAG Context]
    Simulates a mouse hover (mouseover) effect on the target.
    
    How to Use:
    - Useful for triggering CSS ':hover' styles, opening dynamic menus, or revealing tooltips.
    
    Keywords: mouse hover, mouseover, hover menu, reveal hidden.
    """
    from mcp_servers.playwright_server.tools import input_ops
    return await input_ops.hover_element(selector)

@mcp.tool()
async def check_checkbox(selector: str, checked: bool = True) -> str: 
    """CHECKS/UNCHECKS checkbox. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.playwright_server.tools import input_ops
    return await input_ops.check_checkbox(selector, checked)

@mcp.tool()
async def select_option(selector: str, value: str) -> str: 
    """SELECTS dropdown option. [ACTION]
    
    [RAG Context]
    Sets the value of a `<select>` dropdown element.
    
    How to Use:
    - 'value' can be the value attribute, label, or index.
    
    Keywords: dropdown choice, set select, combo box, option pick.
    """
    from mcp_servers.playwright_server.tools import input_ops
    return await input_ops.select_option(selector, value)

@mcp.tool()
async def drag_and_drop(source: str, target: str) -> str: 
    """DRAGS element to target. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.playwright_server.tools import input_ops
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
    Retrieves the entire DOM structure of the current page as a raw string. 
    
    How to Use:
    - Use this for deep analysis of page structure or when specific extraction tools fail.
    - Note: For large pages, this can consume significant tokens.
    
    Keywords: view source, dom content, raw html, page structure.
    """
    from mcp_servers.playwright_server.tools import dom_ops
    return await dom_ops.get_page_content()

@mcp.tool()
async def get_element_text(selector: str) -> str: 
    """GETS element text. [DATA]
    
    [RAG Context]
    Extracts the inner text content from a specific DOM element.
    
    How to Use:
    - Useful for reading headlines, prices, descriptions, and labels.
    - Automatically waits for the element to appear.
    
    Keywords: read text, extract content, element value, text scraper.
    """
    from mcp_servers.playwright_server.tools import dom_ops
    return await dom_ops.get_element_text(selector)

@mcp.tool()
async def get_all_text(selector: str) -> List[str]: 
    """GETS text from all matching elements. [DATA]
    
    [RAG Context]
    """
    from mcp_servers.playwright_server.tools import dom_ops
    return await dom_ops.get_all_text(selector)

@mcp.tool()
async def get_attribute(selector: str, attribute: str) -> str: 
    """GETS element attribute. [DATA]
    
    [RAG Context]
    Retrieves the value of a specific attribute (e.g., 'href', 'src', 'alt', 'data-id') from an element.
    
    How to Use:
    - Use to find link destinations ('href') or image sources ('src').
    
    Keywords: element attribute, html properties, link target, image src.
    """
    from mcp_servers.playwright_server.tools import dom_ops
    return await dom_ops.get_element_attribute(selector, attribute)

@mcp.tool()
async def get_all_attributes(selector: str, attribute: str) -> List[str]: 
    """GETS attributes from all matching elements. [DATA]
    
    [RAG Context]
    """
    from mcp_servers.playwright_server.tools import dom_ops
    return await dom_ops.get_all_attributes(selector, attribute)

@mcp.tool()
async def get_table_data(selector: str) -> List[Dict[str, str]]: 
    """EXTRACTS table data. [DATA]
    
    [RAG Context]
    Automatically parses an HTML `<table>` into a structured list of dictionaries.
    
    How to Use:
    - It attempts to map the first row (`<th>`) as keys for the subsequent rows.
    - Powerful for extracting financial data, product grids, or leaderboards.
    
    Keywords: table scraper, row extraction, grid data, structured web data.
    """
    from mcp_servers.playwright_server.tools import dom_ops
    return await dom_ops.get_table_data(selector)

@mcp.tool()
async def evaluate_js(script: str, arg: Any = None) -> Any: 
    """EXECUTES JavaScript. [ACTION]
    
    [RAG Context]
    Runs a custom JavaScript snippet directly within the browser's execution context.
    
    How to Use:
    - Use this for complex interactions not supported by standard tools (e.g., custom animations, complex state inspection, or overriding page variables).
    
    Keywords: js inject, script execute, browser code, advanced interaction.
    """
    from mcp_servers.playwright_server.tools import dom_ops
    return await dom_ops.evaluate_js(script, arg)

@mcp.tool()
async def screenshot(selector: str, path: str) -> str: 
    """CAPTURES element screenshot. [DATA]
    
    [RAG Context]
    """
    from mcp_servers.playwright_server.tools import dom_ops
    return await dom_ops.screenshot_element(selector, path)

@mcp.tool()
async def screenshot_page(path: str) -> str: 
    """CAPTURES page screenshot. [DATA]
    
    [RAG Context]
    Saves a high-quality visual snapshot of the entire current viewport to a file.
    
    How to Use:
    - Provide an absolute path (e.g., '/tmp/screenshot.png').
    - Essential for visual debugging and verifying page layout.
    
    Keywords: screen capture, image capture, visual log, page snapshot.
    """
    from mcp_servers.playwright_server.tools import dom_ops
    return await dom_ops.screenshot_page(path)

# ==========================================
# 4. Network & State
# ==========================================
@mcp.tool()
async def block_resources(resource_types: List[str] = ["image", "stylesheet", "font"]) -> str: 
    """BLOCKS images/css/fonts. [ACTION]
    
    [RAG Context]
    Intercepts and cancels network requests for specific resource types to speed up data extraction and reduce bandwidth.
    
    How to Use:
    - Default: `["image", "stylesheet", "font"]`.
    - Best for: Pure text scraping or when visual appearance doesn't matter.
    - Warning: May break sites that rely on JS-loaded CSS or specific fonts for layout.
    
    Keywords: speed up scraping, bandwidth saver, headless optimization, resource blocker.
    """
    from mcp_servers.playwright_server.tools import network_ops
    return await network_ops.block_resources(resource_types)

@mcp.tool()
async def get_cookies() -> List[Dict[str, Any]]: 
    """GETS cookies. [DATA]
    
    [RAG Context]
    Retrieves all browser cookies for the current session.
    
    How to Use:
    - Essential for session persistence, authentication bypass, or debugging login states.
    
    Keywords: session cookies, auth tokens, browser storage, crawl state.
    """
    from mcp_servers.playwright_server.tools import state_ops
    return await state_ops.get_cookies()

@mcp.tool()
async def set_cookies(cookies: List[Dict[str, Any]]) -> str: 
    """SETS cookies. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.playwright_server.tools import state_ops
    return await state_ops.set_cookies(cookies)

@mcp.tool()
async def clear_cookies() -> str: 
    """CLEARS cookies. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.playwright_server.tools import state_ops
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
    Interacts with elements nested inside `<iframe>` or `<frame>` tags.
    
    How to Use:
    - Provide the 'selector' for the element and the 'frame_name' (or ID) of the target frame.
    - Essential for interacting with cross-domain ads, payment gateways (Stripe/PayPal), or legacy enterprise portals.
    
    Keywords: iframe click, nested element, frame interaction, cross-domain click.
    """
    from mcp_servers.playwright_server.tools import frame_ops
    return await frame_ops.frame_click(selector, frame_name)

@mcp.tool()
async def frame_fill(selector: str, value: str, frame_name: Optional[str] = None) -> str: 
    """FILLS input in frame. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.playwright_server.tools import frame_ops
    return await frame_ops.frame_fill(selector, value, frame_name)

@mcp.tool()
async def handle_dialog(action: str = "accept", prompt_text: Optional[str] = None) -> str: 
    """HANDLES alerts/prompts. [ACTION]
    
    [RAG Context]
    Automatically responds to browser native dialogs like `alert()`, `confirm()`, or `prompt()`.
    
    How to Use:
    - 'action': 'accept' (hits OK) or 'dismiss' (hits Cancel).
    - 'prompt_text': Text to enter into a prompt dialog if applicable.
    
    Keywords: alert handler, confirm bypass, browser dialog, popup response.
    """
    from mcp_servers.playwright_server.tools import dialog_ops
    return await dialog_ops.handle_dialog(action, prompt_text)

@mcp.tool()
async def enable_console() -> str: 
    """CAPTURES console logs. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.playwright_server.tools import dialog_ops
    return await dialog_ops.enable_console_capture()

@mcp.tool()
async def get_console() -> List[str]: 
    """GETS captured logs. [DATA]
    
    [RAG Context]
    """
    from mcp_servers.playwright_server.tools import dialog_ops
    return await dialog_ops.get_console_logs()

# ==========================================
# 6. Device & Deep Extract
# ==========================================
@mcp.tool()
async def set_geolocation(latitude: float, longitude: float) -> str: 
    """SETS fake location. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.playwright_server.tools import device_ops
    return await device_ops.set_geolocation(latitude, longitude)

@mcp.tool()
async def grant_permissions(permissions: List[str]) -> str: 
    """GRANTS permissions. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.playwright_server.tools import device_ops
    return await device_ops.grant_permissions(permissions)

@mcp.tool()
async def extract_links(selector: str = "a", match_pattern: Optional[str] = None) -> List[str]: 
    """EXTRACTS all links. [DATA]
    
    [RAG Context]
    Scans the page and returns a list of all unique destination URLs.
    
    How to Use:
    - 'match_pattern': Optional regex to filter links (e.g., only internal links or specific domains).
    - Primary tool for building Web Crawlers and sitemap generation.
    
    Keywords: link extraction, url crawler, site mapping, hyperlink finder.
    """
    from mcp_servers.playwright_server.tools import extract_ops
    return await extract_ops.extract_links(selector, match_pattern)

@mcp.tool()
async def get_computed_style(selector: str, property: str) -> str: 
    """GETS CSS style. [DATA]
    
    [RAG Context]
    """
    from mcp_servers.playwright_server.tools import extract_ops
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
    Automated accessibility audit using the Axe-core engine. Scans the DOM for violations of WCAG 2.1 guidelines (e.g., missing aria-labels, low contrast, broken focus order).
    
    Keywords: a11y, web standards, inclusive design, wcag audit.
    """
    from mcp_servers.playwright_server.tools import audit_ops
    return await audit_ops.check_accessibility(selector)

@mcp.tool()
async def audit_seo() -> Dict[str, Any]: 
    """CHECKS SEO basics. [DATA]
    
    [RAG Context]
    """
    from mcp_servers.playwright_server.tools import audit_ops
    return await audit_ops.audit_seo()

@mcp.tool()
async def get_performance() -> Dict[str, float]: 
    """GETS performance metrics. [DATA]
    
    [RAG Context]
    Retrieves Core Web Vitals and navigation timings directly from the browser window object.
    
    How to Use:
    - Returns metrics like: `fetchStart`, `domainLookupEnd`, `domContentLoadedEventEnd`, and `loadEventEnd`.
    - Essential for benchmarking page load speeds.
    
    Keywords: page speed, load time, web vitals, performance monitor.
    """
    from mcp_servers.playwright_server.tools import perf_ops
    return await perf_ops.get_performance_metrics()

@mcp.tool()
async def start_tracing(path: str = "trace.zip") -> str: 
    """STARTS trace recording. [ACTION]
    
    [RAG Context]
    Enables detailed Playwright event tracing, which records every network request, DOM snapshot, and script execution.
    
    How to Use:
    - Best for finding elusive bugs in complex browser workflows.
    
    Keywords: trace log, recording, debug trace, event sniffer.
    """
    from mcp_servers.playwright_server.tools import perf_ops
    return await perf_ops.start_tracing(path)

@mcp.tool()
async def stop_tracing(path: str = "trace.zip") -> str: 
    """STOPS trace recording. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.playwright_server.tools import perf_ops
    return await perf_ops.stop_tracing(path)

# ==========================================
# 8. Mocking & Context
# ==========================================
@mcp.tool()
async def mock_api(url_pattern: str, body: Dict[str, Any]) -> str: 
    """MOCKS API response. [ACTION]
    
    [RAG Context]
    Intercepts network requests matching a URL pattern and returns a faked JSON response body.
    
    How to Use:
    - Avoids hitting real backends during development, testing, or to bypass rate limits.
    
    Keywords: api interceptor, stubbing, faking data, test mock.
    """
    from mcp_servers.playwright_server.tools import mock_ops
    return await mock_ops.mock_api_response(url_pattern, body)

@mcp.tool()
async def abort_requests(url_pattern: str) -> str: 
    """ABORTS network requests. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.playwright_server.tools import mock_ops
    return await mock_ops.route_abort(url_pattern)

@mcp.tool()
async def save_session(path: str) -> str: 
    """SAVES browser state/storage. [ACTION]
    
    [RAG Context]
    Exports all current session data (Cookies, LocalStorage, SessionStorage) to a JSON file.
    
    How to Use:
    - Save the session after logging in to reuse the authenticated state later without re-authenticating.
    
    Keywords: snapshot session, backup login, auth persistence, export cookies.
    """
    from mcp_servers.playwright_server.tools import context_ops
    return await context_ops.save_storage_state(path)

@mcp.tool()
async def load_session(path: str) -> str: 
    """LOADS browser state/storage. [ACTION]
    
    [RAG Context]
    Imports previously saved session data to restore login states and cookies.
    
    Keywords: restore session, import cookies, maintain login, session resume.
    """
    from mcp_servers.playwright_server.tools import context_ops
    return await context_ops.load_storage_state(path)

@mcp.tool()
async def get_clipboard() -> str: 
    """READS clipboard. [DATA]
    
    [RAG Context]
    """
    from mcp_servers.playwright_server.tools import clipboard_ops
    return await clipboard_ops.read_clipboard()

@mcp.tool()
async def set_clipboard(text: str) -> str: 
    """WRITES to clipboard. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.playwright_server.tools import clipboard_ops
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
    Generates a PDF document from the current page layout.
    
    How to Use:
    - Useful for archiving reports, saving receipts, or offline documentation.
    
    Keywords: pdf export, save webpage, document generator, print to disk.
    """
    from mcp_servers.playwright_server.tools import visual_ops
    return await visual_ops.print_to_pdf(path, format)

@mcp.tool()
async def screenshot_mask(path: str, mask_selector: str) -> str: 
    """CAPTURES screenshot with mask. [DATA]
    
    [RAG Context]
    Hides sensitive data.
    """
    from mcp_servers.playwright_server.tools import visual_ops
    return await visual_ops.screenshot_mask(path, mask_selector)

@mcp.tool()
async def tap_point(x: float, y: float) -> str: 
    """TAPS coordinates. [ACTION]
    
    [RAG Context]
    Mobile emulation.
    """
    from mcp_servers.playwright_server.tools import gesture_ops
    return await gesture_ops.tap_point(x, y)

@mcp.tool()
async def swipe(x_start: float, y_start: float, x_end: float, y_end: float) -> str: 
    """SWIPES across screen. [ACTION]
    
    [RAG Context]
    Mobile emulation.
    """
    from mcp_servers.playwright_server.tools import gesture_ops
    return await gesture_ops.swipe(x_start, y_start, x_end, y_end)

# ==========================================
# 10. Wait & Assert (Hyper)
# ==========================================
@mcp.tool()
async def wait_for_selector(selector: str, state: str = "visible", timeout: int = 30000) -> str: 
    """WAITS for element presence. [ACTION]
    
    [RAG Context]
    Pauses execution until a specific DOM element appears or changes state (visible, hidden, attached, detached).
    
    How to Use:
    - Essential for reliable Automation on dynamic pages with AJAX loading.
    
    Keywords: conditional wait, element presence, dynamic loading sync.
    """
    from mcp_servers.playwright_server.tools import wait_ops
    return await wait_ops.wait_for_selector(selector, state, timeout)

@mcp.tool()
async def wait_for_url(url_regex: str, timeout: int = 30000) -> str: 
    """WAITS for URL match. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.playwright_server.tools import wait_ops
    return await wait_ops.wait_for_url(url_regex, timeout)

@mcp.tool()
async def wait_for_function(function_body: str, arg: Any = None) -> str: 
    """WAITS for JS condition. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.playwright_server.tools import wait_ops
    return await wait_ops.wait_for_function(function_body, arg)

@mcp.tool()
async def assert_title(expected: str) -> str: 
    """VERIFIES page title. [DATA]
    
    [RAG Context]
    Test assertion.
    """
    from mcp_servers.playwright_server.tools import assert_ops
    return await assert_ops.assert_title(expected)

@mcp.tool()
async def assert_text(text: str) -> str: 
    """VERIFIES text presence. [DATA]
    
    [RAG Context]
    Test assertion.
    """
    from mcp_servers.playwright_server.tools import assert_ops
    return await assert_ops.assert_text_present(text)

@mcp.tool()
async def assert_count(selector: str, min_count: int) -> str: 
    """VERIFIES element count. [DATA]
    
    [RAG Context]
    Test assertion.
    """
    from mcp_servers.playwright_server.tools import assert_ops
    return await assert_ops.assert_element_count(selector, min_count)

# ==========================================
# 11. Browser Infra (Hyper)
# ==========================================
@mcp.tool()
async def launch_browser(browser_type: str = "chromium") -> str: 
    """STARTS browser instance. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.playwright_server.tools import browser_ops
    return await browser_ops.launch_browser(browser_type)

@mcp.tool()
async def get_browser_info() -> Dict[str, str]: 
    """GETS browser metadata. [DATA]
    
    [RAG Context]
    Version, user agent.
    """
    from mcp_servers.playwright_server.tools import browser_ops
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
    A "Super Tool" that allows multiple browser operations (navigation, clicks, typing) to be submitted in a single tool call as a list of dictionaries.
    
    How to Use:
    - Significantly reduces latency and round-trip overhead for multi-step browser scenarios.
    
    Keywords: action list, batch browser, macro execution, chained steps.
    """
    from mcp_servers.playwright_server.tools import chain_ops
    return await chain_ops.execute_browser_chain(steps)

@mcp.tool()
async def scrape_infinite_scroll(item_selector: str, max_scrolls: int = 10) -> str: 
    """SCRAPES infinite scroll pages. [ACTION]
    
    [RAG Context]
    A specialized "Super Tool" for social media feeds (Twitter, LinkedIn) and modern e-commerce sites. It automatically scrolls to the bottom of the page repeatedly to trigger lazy-loading of content.
    
    How to Use:
    - Provide the 'item_selector' for the repeated elements (e.g., 'div.tweet-content').
    - 'max_scrolls' limits the depth of the extraction.
    
    Keywords: twitter scraper, linkedin scrape, lazy loading, auto scroll, feed extraction.
    """
    from mcp_servers.playwright_server.tools import scraper_ops
    return await scraper_ops.scrape_infinite_scroll(item_selector, max_scrolls)

@mcp.tool()
async def scrape_pagination(next_button_selector: str, item_selector: str, max_pages: int = 5) -> Dict[str, Any]: 
    """SCRAPES paginated lists. [ACTION]
    
    [RAG Context]
    A specialized "Super Tool" for multi-page search results or catalog listings. It collects items from the current page, clicks the 'Next' button, and repeats the process.
    
    Keywords: search results scraper, catalog extractor, result crawler, web harvesting.
    """
    from mcp_servers.playwright_server.tools import scraper_ops
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

