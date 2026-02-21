from __future__ import annotations
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
import random
from shared.logging.main import get_logger

logger = get_logger(__name__)

# User-Agent pool for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def _fetch_with_retry(url: str, timeout: int, headers: dict) -> httpx.Response:
    """Fetch URL with retry logic."""
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response

async def fetch_url_tool(url: str, timeout: int = 30, headers: dict = {}) -> str:
    """Fetch URL content via HTTP GET request."""
    if not url: return "Error: URL is required"
    
    # Build headers with User-Agent rotation
    req_headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        **headers
    }
    
    try:
        response = await _fetch_with_retry(url, timeout, req_headers)
        content_type = response.headers.get("content-type", "")
        
        # Handle different content types
        if "application/json" in content_type:
            text = response.text
        elif "text/" in content_type or "html" in content_type:
            text = response.text
        else:
            text = f"[Binary content: {content_type}, {len(response.content)} bytes]"
        
        # Truncate if too long
        max_length = 50000
        if len(text) > max_length:
            text = text[:max_length] + f"\n\n[Truncated: {len(text)} chars total]"
        
        return text
        
    except httpx.HTTPStatusError as e:
        return f"HTTP Error {e.response.status_code}: {e.response.reason_phrase}"
    except httpx.TimeoutException:
        return f"Timeout after {timeout}s fetching {url}"
    except Exception as e:
        return f"Error: {str(e)}"
