from mcp_servers.ddg_search_server.ddg_client import DDGClient
from typing import List, Any, Optional

# ==========================================
# Image Search
# ==========================================
async def search_images(query: str, size: Optional[str] = None, type_image: Optional[str] = None, layout: Optional[str] = None, license_image: Optional[str] = None, max_results: int = 10) -> List[Any]:
    """
    General image search with filters.
    size: Small, Medium, Large, Wallpaper
    type_image: photo, clipart, gif, transparent
    layout: Square, Tall, Wide
    license_image: any, Public, Share, ShareCommercially, Modify, ModifyCommercially
    """
    return await DDGClient.images(query, size=size, type_image=type_image, layout=layout, license_image=license_image, max_results=max_results)

async def find_clipart(query: str, max_results: int = 10) -> List[Any]:
    return await DDGClient.images(query, type_image="clipart", max_results=max_results)

async def find_gifs(query: str, max_results: int = 10) -> List[Any]:
    return await DDGClient.images(query, type_image="gif", max_results=max_results)

async def find_transparent(query: str, max_results: int = 10) -> List[Any]:
    return await DDGClient.images(query, type_image="transparent", max_results=max_results)

async def find_wallpapers(query: str, max_results: int = 10) -> List[Any]:
    return await DDGClient.images(query, size="Wallpaper", max_results=max_results)

async def find_creative_commons(query: str, max_results: int = 10) -> List[Any]:
    # "Share" roughly maps to CC
    return await DDGClient.images(query, license_image="Share", max_results=max_results)

async def find_people_images(query: str, max_results: int = 10) -> List[Any]:
    # Heuristic: Tall layout often used for portraits/people
    return await DDGClient.images(query, layout="Tall", max_results=max_results)

async def find_icons(query: str, max_results: int = 10) -> List[Any]:
    return await DDGClient.images(query, size="Small", max_results=max_results)

async def find_red_images(query: str, max_results: int = 10) -> List[Any]:
    return await DDGClient.images(query, color="Red", max_results=max_results)

async def find_blue_images(query: str, max_results: int = 10) -> List[Any]:
    return await DDGClient.images(query, color="Blue", max_results=max_results)

# ==========================================
# Video Search
# ==========================================
async def search_videos(query: str, resolution: Optional[str] = None, duration: Optional[str] = None, max_results: int = 10) -> List[Any]:
    """
    General video search.
    resolution: high, standard
    duration: short, medium, long
    """
    return await DDGClient.videos(query, resolution=resolution, duration=duration, max_results=max_results)

async def find_short_videos(query: str, max_results: int = 10) -> List[Any]:
    return await DDGClient.videos(query, duration="short", max_results=max_results)

async def find_long_videos(query: str, max_results: int = 10) -> List[Any]:
    return await DDGClient.videos(query, duration="long", max_results=max_results)

async def find_high_res_videos(query: str, max_results: int = 10) -> List[Any]:
    return await DDGClient.videos(query, resolution="high", max_results=max_results)

async def find_cc_videos(query: str, max_results: int = 10) -> List[Any]:
    return await DDGClient.videos(query, license_videos="creativeCommon", max_results=max_results)
