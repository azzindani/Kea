import asyncio
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext, Page
import structlog

logger = structlog.get_logger()

class BrowserSession:
    """
    Singleton-like manager for a persistent Playwright session.
    Keeps the browser open across multiple tool calls.
    """
    _instance = None
    _playwright: Optional[Playwright] = None
    _browser: Optional[Browser] = None
    _context: Optional[BrowserContext] = None
    _active_page: Optional[Page] = None
    
    @classmethod
    async def initialize(cls, headless: bool = True):
        if cls._playwright:
            return
            
        logger.info("initializing_playwright_session", headless=headless)
        cls._playwright = await async_playwright().start()
        
        # Launch options - we can make this configurable later
        cls._browser = await cls._playwright.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-setuid-sandbox"] 
        )
        
        # Create default context with useful defaults
        cls._context = await cls._browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Create first page
        cls._active_page = await cls._context.new_page()
        logger.info("playwright_session_ready")

    @classmethod
    async def get_page(cls) -> Page:
        """Get the currently active page. Initializes if necessary."""
        if not cls._browser:
            await cls.initialize()
            
        # Ensure we have a context
        if not cls._context:
             cls._context = await cls._browser.new_context()
             
        # Ensure we have at least one page
        if not cls._context.pages:
            cls._active_page = await cls._context.new_page()
        else:
            # Simple strategy: use the last opened page or the tracked active one
            # If the tracked active page is closed, switch to the last one
            if cls._active_page is None or cls._active_page.is_closed():
                cls._active_page = cls._context.pages[-1]
                
        return cls._active_page

    @classmethod
    async def new_page(cls) -> Page:
        if not cls._context: await cls.initialize()
        cls._active_page = await cls._context.new_page()
        return cls._active_page

    @classmethod
    async def close(cls):
        """Cleanup resources."""
        if cls._context:
            await cls._context.close()
        if cls._browser:
            await cls._browser.close()
        if cls._playwright:
            await cls._playwright.stop()
            
        cls._context = None
        cls._browser = None
        cls._playwright = None
        logger.info("playwright_session_closed")

    @classmethod
    async def get_context(cls) -> BrowserContext:
        if not cls._context: await cls.initialize()
        return cls._context
