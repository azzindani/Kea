from mcp_servers.playwright_server.tools import (
    nav_ops, input_ops, dom_ops, network_ops, state_ops, 
    frame_ops, dialog_ops, device_ops, extract_ops,
    audit_ops, perf_ops, mock_ops, context_ops, clipboard_ops,
    visual_ops, gesture_ops, wait_ops, assert_ops, browser_ops
)
import structlog
from typing import List, Dict, Any, Optional

logger = structlog.get_logger()

# Map string action names to actual functions
OP_MAP = {
    # Nav
    'goto': nav_ops.goto_page,
    'back': nav_ops.go_back,
    'reload': nav_ops.reload_page,
    'create_tab': nav_ops.create_tab,
    'close_tab': nav_ops.close_tab,
    
    # Input
    'click': input_ops.click_element,
    'type': input_ops.type_text,
    'fill': input_ops.fill_input,
    'press': input_ops.press_key,
    'hover': input_ops.hover_element,
    'check': lambda **k: input_ops.check_checkbox(checked=True, **k),
    'uncheck': lambda **k: input_ops.check_checkbox(checked=False, **k),
    'select': input_ops.select_option,
    
    # DOM / Extraction
    'get_text': dom_ops.get_element_text,
    'get_all_text': dom_ops.get_all_text,
    'get_attr': dom_ops.get_element_attribute,
    'get_all_attr': dom_ops.get_all_attributes,
    'get_table': dom_ops.get_table_data,
    'count': dom_ops.count_elements,
    'screenshot': dom_ops.screenshot_element,
    'screenshot_page': dom_ops.screenshot_page,
    'eval': dom_ops.evaluate_js,
    
    # Network
    'block': network_ops.block_resources,
    
    # State
    'clear_cookies': state_ops.clear_cookies,

    # Frames
    'frame_click': frame_ops.frame_click,
    'frame_fill': frame_ops.frame_fill,
    'frame_text': frame_ops.frame_get_text,
    
    # Dialogs
    'handle_dialog': dialog_ops.handle_dialog,
    'enable_console': dialog_ops.enable_console_capture,
    'get_console': dialog_ops.get_console_logs,
    
    # Device
    'set_geo': device_ops.set_geolocation,
    'grant_perms': device_ops.grant_permissions,
    'emulate': device_ops.emulate_media,

    # Extract
    'get_style': extract_ops.get_computed_style,
    'get_box': extract_ops.get_bounding_box,
    'get_links': extract_ops.extract_links,
    'get_images': extract_ops.extract_images,

    # Audit
    'audit_a11y': audit_ops.check_accessibility,
    'audit_seo': audit_ops.audit_seo,

    # Perf
    'metrics': perf_ops.get_performance_metrics,
    'trace_start': perf_ops.start_tracing,
    'trace_stop': perf_ops.stop_tracing,

    # Mock
    'mock': mock_ops.mock_api_response,
    'route_abort': mock_ops.route_abort,
    'unroute': mock_ops.unroute,

    # Context
    'save_state': context_ops.save_storage_state,
    'load_state': context_ops.load_storage_state,

    # Clipboard
    'copy': clipboard_ops.write_clipboard,
    'paste': clipboard_ops.read_clipboard,

    # Visual (New)
    'pdf': visual_ops.print_to_pdf,
    'screenshot_mask': visual_ops.screenshot_mask,

    # Gestures (New)
    'tap': gesture_ops.tap_point,
    'swipe': gesture_ops.swipe,

    # Waits (New)
    'wait_selector': wait_ops.wait_for_selector,
    'wait_url': wait_ops.wait_for_url,
    'wait_func': wait_ops.wait_for_function,
    'wait_time': wait_ops.explicit_wait,

    # Assert (New)
    'assert_title': assert_ops.assert_title,
    'assert_text': assert_ops.assert_text_present,
    'assert_count': assert_ops.assert_element_count,
    'assert_visible': assert_ops.assert_element_visible,

    # Browser (New)
    'restart': browser_ops.launch_browser,
    'info': browser_ops.get_browser_info
}

async def execute_browser_chain(steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Execute a sequence of browser actions.
    steps: [{"action": "goto", "args": {"url": "..."}}, {"action": "click", ...}]
    Returns list of results for each step.
    """
    results = []
    
    for i, step in enumerate(steps):
        action = step.get("action")
        args = step.get("args", {})
        
        if action not in OP_MAP:
            results.append({"step": i, "action": action, "status": "error", "message": "Unknown action"})
            continue
            
        try:
            func = OP_MAP[action]
            # Call function with args
            res = await func(**args)
            results.append({"step": i, "action": action, "status": "success", "result": res})
        except Exception as e:
            results.append({"step": i, "action": action, "status": "error", "message": str(e)})
            
    return results
