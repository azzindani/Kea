from mcp_servers.playwright_server.session_manager import BrowserSession
from playwright.async_api import Frame, Page
from typing import Optional, List, Dict, Any

async def get_frame(name: Optional[str] = None, url: Optional[str] = None) -> Optional[Frame]:
    """Helper to locate a frame."""
    page = await BrowserSession.get_page()
    if name:
        return page.frame(name=name)
    if url:
        return page.frame(url=url)
    return None

async def frame_click(selector: str, frame_name: Optional[str] = None, frame_url: Optional[str] = None, timeout: int = 5000) -> str:
    """Click an element inside a specific iframe."""
    frame = await get_frame(frame_name, frame_url)
    if not frame:
        return "Error: Frame not found"
    
    try:
        await frame.click(selector, timeout=timeout)
        return f"Clicked {selector} in frame"
    except Exception as e:
        return f"Error clicking in frame: {str(e)}"

async def frame_fill(selector: str, value: str, frame_name: Optional[str] = None, frame_url: Optional[str] = None) -> str:
    """Fill input inside a specific iframe."""
    frame = await get_frame(frame_name, frame_url)
    if not frame:
        return "Error: Frame not found"
    
    try:
        await frame.fill(selector, value)
        return f"Filled {selector} in frame"
    except Exception as e:
        return f"Error filling in frame: {str(e)}"

async def frame_get_text(selector: str, frame_name: Optional[str] = None, frame_url: Optional[str] = None) -> str:
    """Get text from element inside a frame."""
    frame = await get_frame(frame_name, frame_url)
    if not frame:
        return "Error: Frame not found"
    
    try:
        return await frame.text_content(selector) or ""
    except Exception as e:
        return f"Error getting text in frame: {str(e)}"

async def list_frames() -> List[Dict[str, str]]:
    """List all frames in the current page."""
    page = await BrowserSession.get_page()
    frames = page.frames
    return [{"name": f.name, "url": f.url} for f in frames]
