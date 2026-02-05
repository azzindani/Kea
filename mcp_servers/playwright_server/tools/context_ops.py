from mcp_servers.playwright_server.session_manager import BrowserSession
from typing import Optional, Dict, Any, List

async def save_storage_state(path: str) -> str:
    """
    Save the current context state (cookies, local storage) to a JSON file.
    Useful for saving successful login sessions.
    """
    context = await BrowserSession.get_context()
    await context.storage_state(path=path)
    return f"Storage state saved to {path}"

async def load_storage_state(path: str) -> str:
    """
    Load a saved storage state.
    Note: Playwright usually requires this at Context Creation.
    We might need to create a new context to apply this.
    For this server, we'll try initializing a NEW context with this state.
    """
    # This effectively resets the session with the loaded state
    # Calling initialize again might ignore if already inited, 
    # so we explicitly ask session manager to create new context/page?
    # Actually, let's close the current context and make a new one with the state.
    
    browser = BrowserSession._browser
    if not browser:
        return "Error: Browser not initialized."
    
    # Close old context
    if BrowserSession._context:
        await BrowserSession._context.close()
        
    # Create new with state
    context = await browser.new_context(storage_state=path)
    BrowserSession._context = context
    
    # New page
    BrowserSession._active_page = await context.new_page()
    
    return f"Context recreated with storage state from {path}"

async def create_named_context(name: str) -> str:
    """
    Create a separate browser context (e.g. 'admin' vs 'user').
    (Note: The simple SessionManager currently tracks one active context. 
    Managing named contexts adds complexity. For now, we'll mimic it by
    restarting session or just logging that multi-context management 
    via RPC requires a more complex manager. We'll skip this for V1 Ultimate).
    """
    return "Not implemented in V1. Use save/load storage state to switch profiles."
