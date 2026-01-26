from mcp_servers.playwright_server.session_manager import BrowserSession
from typing import Optional, List, Dict, Any

async def set_geolocation(latitude: float, longitude: float) -> str:
    """Set the geolocation."""
    context = await BrowserSession.get_context()
    await context.set_geolocation({"latitude": latitude, "longitude": longitude})
    await context.grant_permissions(["geolocation"])
    return f"Geolocation set to {latitude}, {longitude}"

async def set_timezone(timezone_id: str) -> str:
    """Set the timezone (e.g., 'America/New_York'). Requires context restart usually? Playwright supports dynamic?"""
    # Playwright allows setting timezone at context level. 
    # Ideally should be done at creation, but let's see if we can create a new context if needed
    # or if we assume the user accepts a new context.
    # Actually, BrowserContext cannot change timezone after creation easily without recreation.
    # But we can try to emulate logic if mostly for JS `Date`
    return "Note: Timezone is best set at session start. Changing mid-session requires recreating context."

async def grant_permissions(permissions: List[str], origin: Optional[str] = None) -> str:
    """Grant permissions (e.g. ['camera', 'microphone'])."""
    context = await BrowserSession.get_context()
    await context.grant_permissions(permissions, origin=origin)
    return f"Granted permissions: {permissions}"

async def clear_permissions() -> str:
    """Clear all permissions."""
    context = await BrowserSession.get_context()
    await context.clear_permissions()
    return "Permissions cleared"

async def emulate_media(media: str = None, color_scheme: str = None) -> str:
    """
    Emulate media type or color scheme.
    media: 'screen', 'print'
    color_scheme: 'light', 'dark', 'no-preference'
    """
    page = await BrowserSession.get_page()
    await page.emulate_media(media=media, color_scheme=color_scheme)
    return f"Emulated media={media}, color_scheme={color_scheme}"
