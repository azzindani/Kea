
import os
import json
import time
import httpx
from typing import List

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CACHE_EXPIRY = 86400 * 7  # 7 days

from shared.logging import get_logger

logger = get_logger(__name__)

class TickerCache:
    """
    Manages dynamic lists of tickers.
    PURE LOGIC NO DATA: Fetches from external sources or loads local JSON.
    """
    
    # Real-world raw URLs for ticker lists (Sourced from public datasets)
    SOURCES = {
        "US": "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all/all_tickers.txt"
    }

    def __init__(self):
        os.makedirs(CACHE_DIR, exist_ok=True)
        
    async def get_tickers_for_country(self, country_code: str) -> List[str]:
        """Get known tickers for a country code (ISO 2)."""
        code = country_code.upper()
        
        # 1. Try Cache / Data File
        cached = self._load_cache(code)
        if cached:
            return cached
            
        # 2. Try Network Fetch (If source known)
        if self.SOURCES.get(code):
             try:
                 logger.info(f"Fetching ticker list for {code} from network...")
                 tickers = await self._fetch_from_source(self.SOURCES[code])
                 if tickers:
                     self._save_cache(code, tickers)
                     return tickers
             except Exception as e:
                 logger.error(f"Fetch failed for {code}: {e}")
        
        # 3. No Hardcoded Fallback - Return Empty if nothing found.
        # This forces the system to rely on external data or explicit updates.
        return []

    async def _fetch_from_source(self, url: str) -> List[str]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            resp.raise_for_status()
            text = resp.text
            # delimiters often newline or comma
            if "," in text and "\n" not in text:
                return [t.strip() for t in text.split(",") if t.strip()]
            return [t.strip() for t in text.split("\n") if t.strip()]

    def _load_cache(self, country: str) -> List[str] | None:
        path = os.path.join(CACHE_DIR, f"{country}.json")
        if not os.path.exists(path):
            return None
            
        try:
            # Check age
            if time.time() - os.path.getmtime(path) > CACHE_EXPIRY:
                return None
                
            with open(path, "r") as f:
                data = json.load(f)
                return data.get("tickers")
        except:
            return None

    def _save_cache(self, country: str, tickers: List[str]):
        path = os.path.join(CACHE_DIR, f"{country}.json")
        with open(path, "w") as f:
            json.dump({"last_updated": time.time(), "count": len(tickers), "tickers": tickers}, f)
            
    def update_custom_list(self, list_name: str, tickers: List[str]):
        """Allow user/system to manually inject a list (e.g. from a file upload)."""
        self._save_cache(list_name.upper(), tickers)
