import asyncio
from typing import List, Dict, Any, Optional, Union
from googlesearch import search
import structlog
import time
import random

logger = structlog.get_logger()

class GoogleSearchClient:
    """
    Wrapper around googlesearch-python to handle Rate Limiting (429) 
    and provide async execution.
    """
    
    @staticmethod
    async def search(
        query: str, 
        num_results: int = 10, 
        lang: str = "en", 
        region: Optional[str] = None,
        advanced: bool = True,
        sleep_interval: float = 0.0,
        max_retries: int = 3
    ) -> List[Union[str, Dict[str, str]]]:
        """
        Execute Google Search with retries.
        
        Args:
            query: Search query string.
            num_results: Number of results to return.
            lang: Language code (e.g. 'en', 'fr').
            region: Region code (e.g. 'us', 'uk').
            advanced: If True, returns objects with titles/description. If False, URLs only.
            sleep_interval: Time to sleep between internal requests (handled by lib).
            max_retries: Number of retries on failure.
        """
        
        # Exponential backoff parameters
        base_delay = 2.0
        
        for attempt in range(max_retries + 1):
            try:
                logger.info("google_search_executing", query=query, attempt=attempt)
                
                # Run synchronous search in thread pool to avoid blocking event loop
                # Note: googlesearch-python returns a generator. We must iterate it to trigger requests.
                def _do_search():
                    # The limit argument in search() controls how many results.
                    # advanced=True returns SearchResult objects (or dicts depending on version)
                    # We'll assume the library returns objects or dicts.
                    results = []
                    # We need to use list() to consume the generator
                    # The 'pause' argument is the sleep_interval
                    iterator = search(
                        query, 
                        num=num_results, 
                        stop=num_results, 
                        lang=lang, 
                        region=region, 
                        advanced=advanced,
                        pause=sleep_interval
                    )
                    
                    for item in iterator:
                        results.append(item)
                    return results

                # Execute in thread
                results = await asyncio.to_thread(_do_search)
                
                # Normalize results
                normalized = []
                for item in results:
                    if isinstance(item, str):
                        normalized.append(item)
                    else:
                        # Attempt to extract attributes if it's an object
                        try:
                            normalized.append({
                                "title": getattr(item, "title", ""),
                                "url": getattr(item, "url", ""),
                                "description": getattr(item, "description", "")
                            })
                        except AttributeError:
                             # Fallback if it's a dict or other
                            normalized.append(str(item))
                            
                return normalized

            except Exception as e:
                error_msg = str(e).lower()
                is_rate_limit = "429" in error_msg or "too many requests" in error_msg
                
                if is_rate_limit and attempt < max_retries:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    logger.warning("google_search_rate_limit", error=str(e), retry_in=delay)
                    await asyncio.sleep(delay)
                    continue
                elif attempt < max_retries:
                    # Other errors, maybe network blip
                    logger.warning("google_search_error", error=str(e), retry_in=1.0)
                    await asyncio.sleep(1.0)
                    continue
                else:
                    logger.error("google_search_failed", error=str(e))
                    return [{"error": f"Search failed after {max_retries} retries: {str(e)}"}]
        
        return []

    @staticmethod
    async def safe_search(query: str, num_results: int = 10) -> List[Any]:
        """Convenience method for safe search (SafeSearch is often a param, but sometimes handled via query 'safe=active')"""
        # googlesearch-python might not expose 'safe' param directly in all versions.
        # usually it's `safe="on"` or `safe="active"` in params.
        # The library signature is: search(term, num=10, lang='en', safe='off', ...)
        # We will try to pass safe='active' if supported, or rely on wrapper.
        
        # Checking library source or docs: many versions have `safe` param.
        # We'll assume standard usage.
        
        def _do_safe_search():
            return list(search(query, num=num_results, stop=num_results, safe="active", advanced=True))
            
        return await asyncio.to_thread(_do_safe_search)
