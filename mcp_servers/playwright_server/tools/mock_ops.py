from mcp_servers.playwright_server.session_manager import BrowserSession
from playwright.async_api import Route
from typing import Optional, Dict, Any, Union
import json

async def mock_api_response(url_pattern: str, body: Union[Dict, str], status: int = 200, headers: Optional[Dict[str, str]] = None) -> str:
    """
    Mock a network response for a specific URL pattern (glob or regex).
    body: dict (returned as json) or str (raw body).
    """
    context = await BrowserSession.get_context()
    
    async def handle_route(route: Route):
        json_body = body if isinstance(body, dict) else None
        raw_body = body if isinstance(body, str) else None
        
        await route.fulfill(
            status=status,
            json=json_body,
            body=raw_body,
            headers=headers
        )
        
    await context.route(url_pattern, handle_route)
    return f"Mocking established for {url_pattern}"

async def route_abort(url_pattern: str, error_code: str = "failed") -> str:
    """
    Force a request to fail.
    error_code: 'aborted', 'accessdenied', 'addressunreachable', 'connectionaborted', 'connectionclosed', 'connectionfailed', 'connectionrefused', 'connectionreset', 'internetdisconnected', 'namenotresolved', 'timedout', 'failed'
    """
    context = await BrowserSession.get_context()
    await context.route(url_pattern, lambda route: route.abort(error_code))
    return f"Aborting requests to {url_pattern} with {error_code}"

async def unroute(url_pattern: str) -> str:
    """Remove a route handler (stop mocking)."""
    context = await BrowserSession.get_context()
    await context.unroute(url_pattern)
    return f"Unrouted {url_pattern}"
