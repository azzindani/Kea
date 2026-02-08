from mcp_servers.playwright_server.session_manager import BrowserSession
from typing import Optional, Dict

async def launch_browser(browser_type: str = "chromium", headless: bool = True) -> str:
    """
    Launch/Switch browser engine.
    browser_type: 'chromium', 'firefox', 'webkit'
    Warning: This closes the current session.
    """
    # Close current
    await BrowserSession.close()
    
    # Initialize implementation is in SessionManager, but currently hardcoded to chromium launch options.
    # We need to enhance SessionManager to accept browser_type, OR we just modify logic here to support it?
    # Modifying SessionManager logic from here is cleaner via a restart method.
    
    # Actually, let's update SessionManager on the fly? 
    # Or just instruct user to use a specialized tool that re-inits the loop.
    # Ideally, we should update init signature in session_manager, but I can't easily edit that file 
    # without full replacement.
    # Strategy: We will monkey-patch or reset private vars and call specialized launch logic here? 
    # No, proper way: SessionManager needs 'restart' method with params.
    # Since I cannot easily edit SessionManager now slightly, I will implement a 're-init' logic here that basically duplicates init but with different browser type call.
    
    from playwright.async_api import async_playwright
    
    BrowserSession._instance = None # Reset
    # ... actually SessionManager.initialize handles singleton check.
    # We need to force close first.
    
    # We'll implement a simplified re-launcher here for now that sets private vars of BrowserSession
    import structlog
    logger = structlog.get_logger()
    logger.info("switching_browser", type=browser_type)
    
    playwright = await async_playwright().start()
    BrowserSession._playwright = playwright
    
    import sys
    import asyncio
    
    try:
        if browser_type == "firefox":
            browser = await playwright.firefox.launch(headless=headless)
        elif browser_type == "webkit":
            browser = await playwright.webkit.launch(headless=headless)
        else:
            browser = await playwright.chromium.launch(headless=headless, args=["--no-sandbox"])
    except Exception as e:
        if "Executable doesn't exist" in str(e):
            logger.info("Browser executable missing, installing...", browser=browser_type)
            # Install specific browser to save time/space
            cmd = [sys.executable, "-m", "playwright", "install", browser_type]
            proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            await proc.communicate()
            
            # Retry launch
            if browser_type == "firefox":
                browser = await playwright.firefox.launch(headless=headless)
            elif browser_type == "webkit":
                browser = await playwright.webkit.launch(headless=headless)
            else:
                browser = await playwright.chromium.launch(headless=headless, args=["--no-sandbox"])
        else:
            raise e
        
    BrowserSession._browser = browser
    BrowserSession._context = await browser.new_context(viewport={"width": 1280, "height": 720})
    BrowserSession._active_page = await BrowserSession._context.new_page()
    
    return f"Browser restarted as {browser_type}"

async def get_browser_info() -> Dict[str, str]:
    """Get info about current browser session."""
    if not BrowserSession._browser:
        return {"status": "not_running"}
    
    return {
        "status": "running",
        "version": BrowserSession._browser.version,
        "contexts": str(len(BrowserSession._browser.contexts)),
        "is_connected": str(BrowserSession._browser.is_connected())
    }
