from mcp_servers.playwright_server.session_manager import BrowserSession
from playwright.async_api import Dialog, Page
from typing import List, Dict, Any, Optional

# Track logs in memory for retrieval
_console_logs: List[str] = []

def _console_handler(msg):
    _console_logs.append(f"[{msg.type}] {msg.text}")

async def enable_console_capture() -> str:
    """Start capturing console logs."""
    page = await BrowserSession.get_page()
    # Remove existing to avoid duplicates if called multiple times
    page.remove_listener("console", _console_handler)
    page.on("console", _console_handler)
    return "Console capture enabled"

async def get_console_logs() -> List[str]:
    """Get captured logs and clear the buffer."""
    global _console_logs
    logs = list(_console_logs)
    _console_logs = []
    return logs

async def handle_dialog(action: str = "accept", prompt_text: Optional[str] = None) -> str:
    """
    Handle the next dialog (alert, confirm, prompt).
    action: 'accept' or 'dismiss'
    prompt_text: text to enter for prompt
    """
    page = await BrowserSession.get_page()
    
    async def dialog_handler(dialog: Dialog):
        if action == "accept":
            await dialog.accept(prompt_text)
        else:
            await dialog.dismiss()
            
    # Set handler for *next* dialog
    page.once("dialog", dialog_handler)
    return f"Prepared to {action} next dialog"
