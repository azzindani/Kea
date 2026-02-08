import asyncio
from typing import List, Dict, Any, Optional
from duckduckgo_search import DDGS
import structlog
import warnings

# Suppress "renamed to ddgs" warning
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*renamed to ddgs.*")

logger = structlog.get_logger()

class DDGClient:
    """
    Async Wrapper around duckduckgo_search (DDGS).
    Executes blocking calls in a thread pool.
    """
    
    @staticmethod
    async def _exec_sync(func_name: str, *args, **kwargs) -> List[Dict[str, Any]]:
        """Generic executor for DDGS methods."""
        
        def _run():
            # DDGS is a context manager, best to use it as such to handle sessions
            with DDGS() as ddgs:
                method = getattr(ddgs, func_name)
                # Execute method and return generator results as list
                # Note: Some methods return generators, others distinct objects.
                # convert to list immediately to ensure execution inside thread
                return list(method(*args, **kwargs))

        try:
            # Run in thread
            return await asyncio.to_thread(_run)
        except Exception as e:
            logger.error(f"ddg_{func_name}_failed", error=str(e), args=args, kwargs=kwargs)
            return [{"error": str(e)}]

    @classmethod
    async def text(cls, keywords: str, region: str = "wt-wt", safesearch: str = "moderate", timelimit: Optional[str] = None, max_results: int = 10) -> List[Dict[str, Any]]:
        """Execute text search."""
        return await cls._exec_sync("text", keywords=keywords, region=region, safesearch=safesearch, timelimit=timelimit, max_results=max_results)

    @classmethod
    async def images(cls, keywords: str, region: str = "wt-wt", safesearch: str = "moderate", timelimit: Optional[str] = None, size: Optional[str] = None, color: Optional[str] = None, type_image: Optional[str] = None, layout: Optional[str] = None, license_image: Optional[str] = None, max_results: int = 10) -> List[Dict[str, Any]]:
        """Execute image search."""
        return await cls._exec_sync("images", keywords=keywords, region=region, safesearch=safesearch, timelimit=timelimit, size=size, color=color, type_image=type_image, layout=layout, license_image=license_image, max_results=max_results)

    @classmethod
    async def videos(cls, keywords: str, region: str = "wt-wt", safesearch: str = "moderate", timelimit: Optional[str] = None, resolution: Optional[str] = None, duration: Optional[str] = None, license_videos: Optional[str] = None, max_results: int = 10) -> List[Dict[str, Any]]:
        """Execute video search."""
        return await cls._exec_sync("videos", keywords=keywords, region=region, safesearch=safesearch, timelimit=timelimit, resolution=resolution, duration=duration, license_videos=license_videos, max_results=max_results)

    @classmethod
    async def news(cls, keywords: str, region: str = "wt-wt", safesearch: str = "moderate", timelimit: Optional[str] = None, max_results: int = 10) -> List[Dict[str, Any]]:
        """Execute news search."""
        return await cls._exec_sync("news", keywords=keywords, region=region, safesearch=safesearch, timelimit=timelimit, max_results=max_results)

    @classmethod
    async def maps(cls, keywords: str, place: Optional[str] = None, street: Optional[str] = None, city: Optional[str] = None, county: Optional[str] = None, state: Optional[str] = None, country: Optional[str] = None, postalcode: Optional[str] = None, latitude: Optional[str] = None, longitude: Optional[str] = None, radius: int = 0, max_results: int = 10) -> List[Dict[str, Any]]:
        """Execute maps search."""
        return await cls._exec_sync("maps", keywords=keywords, place=place, street=street, city=city, county=county, state=state, country=country, postalcode=postalcode, latitude=latitude, longitude=longitude, radius=radius, max_results=max_results)

    @classmethod
    async def translate(cls, keywords: str, to: str = "en") -> List[Dict[str, Any]]:
        """Execute translation."""
        return await cls._exec_sync("translate", keywords=keywords, to=to)

    @classmethod
    async def answers(cls, keywords: str) -> List[Dict[str, Any]]:
        """Get instant answers."""
        return await cls._exec_sync("answers", keywords=keywords)
    
    @classmethod
    async def suggestions(cls, keywords: str, region: str = "wt-wt") -> List[Dict[str, Any]]:
        """Get suggestions."""
        return await cls._exec_sync("suggestions", keywords=keywords, region=region)
