# 🔌 Playwright Server

The `playwright_server` is an MCP server providing tools for **Playwright Server** functionality.
It is designed to be used within the Kea ecosystem.

## 🧰 Tools

| Tool | Description | Arguments |
|:-----|:------------|:----------|
| `install_playwright` | Execute install playwright operation | `` |
| `goto_page` | Execute goto page operation | `url: str, timeout: int = 30000, wait_until: str = "domcontentloaded"` |
| `go_back` | Execute go back operation | `` |
| `go_forward` | Execute go forward operation | `` |
| `reload_page` | Execute reload page operation | `` |
| `create_tab` | Execute create tab operation | `` |
| `close_tab` | Execute close tab operation | `` |
| `set_viewport` | Execute set viewport operation | `width: int, height: int` |
| `get_url` | Execute get url operation | `` |
| `click_element` | Execute click element operation | `selector: str, timeout: int = 5000` |
| `type_text` | Execute type text operation | `selector: str, text: str, delay: int = 0` |
| `fill_input` | Execute fill input operation | `selector: str, value: str` |
| `press_key` | Execute press key operation | `key: str` |
| `hover_element` | Execute hover element operation | `selector: str` |
| `check_checkbox` | Execute check checkbox operation | `selector: str, checked: bool = True` |
| `select_option` | Execute select option operation | `selector: str, value: str` |
| `drag_and_drop` | Execute drag and drop operation | `source: str, target: str` |
| `get_page_content` | Execute get page content operation | `` |
| `get_element_text` | Execute get element text operation | `selector: str` |
| `get_all_text` | Execute get all text operation | `selector: str` |
| `get_attribute` | Execute get attribute operation | `selector: str, attribute: str` |
| `get_all_attributes` | Execute get all attributes operation | `selector: str, attribute: str` |
| `get_table_data` | Execute get table data operation | `selector: str` |
| `evaluate_js` | Execute evaluate js operation | `script: str, arg: Any = None` |
| `screenshot` | Execute screenshot operation | `selector: str, path: str` |
| `screenshot_page` | Execute screenshot page operation | `path: str` |
| `block_resources` | Execute block resources operation | `resource_types: List[str] = ["image", "stylesheet", "font"]` |
| `get_cookies` | Execute get cookies operation | `` |
| `set_cookies` | Execute set cookies operation | `cookies: List[Dict[str, Any]]` |
| `clear_cookies` | Execute clear cookies operation | `` |
| `frame_click` | Execute frame click operation | `selector: str, frame_name: Optional[str] = None` |
| `frame_fill` | Execute frame fill operation | `selector: str, value: str, frame_name: Optional[str] = None` |
| `handle_dialog` | Execute handle dialog operation | `action: str = "accept", prompt_text: Optional[str] = None` |
| `enable_console` | Execute enable console operation | `` |
| `get_console` | Execute get console operation | `` |
| `set_geolocation` | Execute set geolocation operation | `latitude: float, longitude: float` |
| `grant_permissions` | Execute grant permissions operation | `permissions: List[str]` |
| `extract_links` | Execute extract links operation | `selector: str = "a", match_pattern: Optional[str] = None` |
| `get_computed_style` | Execute get computed style operation | `selector: str, property: str` |
| `audit_accessibility` | Execute audit accessibility operation | `selector: str = "body"` |
| `audit_seo` | Execute audit seo operation | `` |
| `get_performance` | Execute get performance operation | `` |
| `start_tracing` | Execute start tracing operation | `path: str = "trace.zip"` |
| `stop_tracing` | Execute stop tracing operation | `path: str = "trace.zip"` |
| `mock_api` | Execute mock api operation | `url_pattern: str, body: Dict[str, Any]` |
| `abort_requests` | Execute abort requests operation | `url_pattern: str` |
| `save_session` | Execute save session operation | `path: str` |
| `load_session` | Execute load session operation | `path: str` |
| `get_clipboard` | Execute get clipboard operation | `` |
| `set_clipboard` | Execute set clipboard operation | `text: str` |
| `print_to_pdf` | Execute print to pdf operation | `path: str, format: str = "A4"` |
| `screenshot_mask` | Execute screenshot mask operation | `path: str, mask_selector: str` |
| `tap_point` | Execute tap point operation | `x: float, y: float` |
| `swipe` | Execute swipe operation | `x_start: float, y_start: float, x_end: float, y_end: float` |
| `wait_for_selector` | Execute wait for selector operation | `selector: str, state: str = "visible", timeout: int = 30000` |
| `wait_for_url` | Execute wait for url operation | `url_regex: str, timeout: int = 30000` |
| `wait_for_function` | Execute wait for function operation | `function_body: str, arg: Any = None` |
| `assert_title` | Execute assert title operation | `expected: str` |
| `assert_text` | Execute assert text operation | `text: str` |
| `assert_count` | Execute assert count operation | `selector: str, min_count: int` |
| `launch_browser` | Execute launch browser operation | `browser_type: str = "chromium"` |
| `get_browser_info` | Execute get browser info operation | `` |
| `execute_browser_chain` | Execute execute browser chain operation | `steps: List[Dict[str, Any]]` |
| `scrape_infinite_scroll` | Execute scrape infinite scroll operation | `item_selector: str, max_scrolls: int = 10` |
| `scrape_pagination` | Execute scrape pagination operation | `next_button_selector: str, item_selector: str, max_pages: int = 5` |

## 📦 Dependencies

The following packages are required:
- `playwright`

## 🚀 Usage

This server is automatically discovered by the **MCP Host**. To run it manually:

```bash
uv run python -m mcp_servers.playwright_server.server
```
