from mcp_servers.ddg_search_server.ddg_client import DDGClient
from typing import List, Any, Dict

async def translate_text(text: str, to_lang: str = "en") -> List[Any]:
    """Translate text using DDG translation."""
    return await DDGClient.translate(text, to=to_lang)

async def identify_language(text: str) -> str:
    """
    Identify language by attempting to translate to 'en'.
    The result usually contains 'detected_language'.
    """
    res = await DDGClient.translate(text, to="en")
    if res and len(res) > 0:
        return res[0].get("detected_language", "unknown")
    return "unknown"

# Note: AI Chat in DDG (DuckAssist/Chat) is not fully exposed in the library 
# in a stable way for all versions, often experimental.
# We will omit `ddg_chat` for now to ensure stability as per "dont use dummy data/experimental" requirement implies robustness.
