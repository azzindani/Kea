from mcp_servers.playwright_server.session_manager import BrowserSession

async def read_clipboard() -> str:
    """
    Read text from clipboard.
    Requires context permissions for 'clipboard-read'.
    """
    context = await BrowserSession.get_context()
    await context.grant_permissions(["clipboard-read", "clipboard-write"])
    
    page = await BrowserSession.get_page()
    return await page.evaluate("navigator.clipboard.readText()")

async def write_clipboard(text: str) -> str:
    """Write text to clipboard."""
    context = await BrowserSession.get_context()
    await context.grant_permissions(["clipboard-read", "clipboard-write"])
    
    page = await BrowserSession.get_page()
    await page.evaluate(f"navigator.clipboard.writeText('{text}')")
    return f"Wrote to clipboard: {text[:20]}..."
