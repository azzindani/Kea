from mcp_servers.playwright_server.session_manager import BrowserSession
from playwright.async_api import Route, Request
from typing import Optional, Dict, Any, List

async def block_resources(resource_types: List[str] = ["image", "stylesheet", "font"]) -> str:
    """
    Block specific resource types to speed up loading.
    Common types: 'image', 'stylesheet', 'font', 'media', 'script'.
    """
    context = await BrowserSession.get_context()
    
    async def route_handler(route: Route):
        if route.request.resource_type in resource_types:
            await route.abort()
        else:
            await route.continue_()
            
    await context.route("**/*", route_handler)
    return f"Blocking resources: {resource_types}"

async def set_custom_headers(headers: Dict[str, str]) -> str:
    """Set custom HTTP headers for all requests."""
    context = await BrowserSession.get_context()
    await context.set_extra_http_headers(headers)
    return f"Set {len(headers)} custom headers"

async def set_user_agent(user_agent: str) -> str:
    """Set custom User Agent."""
    # Note: User Agent is usually set at Context creation. 
    # Changing it requires a new context or hacky overrides.
    # For now, we'll try to set the header 'User-Agent'
    return await set_custom_headers({"User-Agent": user_agent})

# Note: Complex interception involves callbacks which are hard to expose 
# as simple RPC tools without a persistent "session ID" for the interceptor.
# We stick to simple blocking and headers for now.
