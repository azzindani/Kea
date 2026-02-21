
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "mcp",
#   "duckduckgo-search",
#   "structlog"
# ]
# ///

from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.ddg_search_server.tools import (
    text_ops, media_ops, news_ops, map_ops, ai_ops, bulk_ops
)
import structlog
from typing import List, Dict, Any, Optional

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging()

mcp = FastMCP("ddg_search_server", dependencies=["duckduckgo_search"])

# ==========================================
# 1. Text Search
# ==========================================
# ==========================================
# 1. Text Search
# ==========================================
@mcp.tool()
async def search_text(query: str, region: str = "wt-wt", safe_search: str = "moderate", time: Optional[str] = None, max_results: int = 100000) -> List[Any]: 
    """SEARCHES text. [ACTION]
    
    [RAG Context]
    General DuckDuckGo text search.
    Returns list of results.
    """
    return await text_ops.search_text(query, region, safe_search, time, max_results)

@mcp.tool()
async def search_private(query: str, max_results: int = 100000) -> List[Any]: 
    """SEARCHES private. [ACTION]
    
    [RAG Context]
    Search with stricter privacy settings.
    Returns list of results.
    """
    return await text_ops.search_private(query, max_results)

@mcp.tool()
async def search_answers(query: str) -> List[Any]: 
    """FETCHES instant answer. [ACTION]
    
    [RAG Context]
    Get instant answer/abstract for query.
    Returns list of results.
    """
    return await text_ops.search_answers(query)

@mcp.tool()
async def search_suggestions(query: str, region: str = "wt-wt") -> List[Any]: 
    """FETCHES suggestions. [ACTION]
    
    [RAG Context]
    Get search query suggestions.
    Returns list of suggestions.
    """
    return await text_ops.search_suggestions(query, region)

@mcp.tool()
async def search_past_day(query: str, max_results: int = 100000) -> List[Any]: 
    """SEARCHES past day. [ACTION]
    
    [RAG Context]
    Search for results from the last 24 hours.
    Returns list of results.
    """
    return await text_ops.search_past_day(query, max_results)

@mcp.tool()
async def search_past_week(query: str, max_results: int = 100000) -> List[Any]: 
    """SEARCHES past week. [ACTION]
    
    [RAG Context]
    Search for results from the last 7 days.
    Returns list of results.
    """
    return await text_ops.search_past_week(query, max_results)

@mcp.tool()
async def search_past_month(query: str, max_results: int = 100000) -> List[Any]: 
    """SEARCHES past month. [ACTION]
    
    [RAG Context]
    Search for results from the last month.
    Returns list of results.
    """
    return await text_ops.search_past_month(query, max_results)

@mcp.tool()
async def search_past_year(query: str, max_results: int = 100000) -> List[Any]: 
    """SEARCHES past year. [ACTION]
    
    [RAG Context]
    Search for results from the last year.
    Returns list of results.
    """
    return await text_ops.search_past_year(query, max_results)

@mcp.tool()
async def search_region(query: str, region: str, max_results: int = 100000) -> List[Any]: 
    """SEARCHES region. [ACTION]
    
    [RAG Context]
    Search within a specific region/country.
    Returns list of results.
    """
    return await text_ops.search_region(query, region, max_results)

@mcp.tool()
async def search_python_docs(query: str, max_results: int = 100000) -> List[Any]: 
    """SEARCHES PyDocs. [ACTION]
    
    [RAG Context]
    Search Python documentation.
    Returns list of results.
    """
    return await text_ops.search_python_docs(query, max_results)

@mcp.tool()
async def search_stackoverflow(query: str, max_results: int = 100000) -> List[Any]: 
    """SEARCHES StackOverflow. [ACTION]
    
    [RAG Context]
    Search Stack Overflow for programming answers.
    Returns list of results.
    """
    return await text_ops.search_stackoverflow(query, max_results)

# ==========================================
# 2. Image Search
# ==========================================
@mcp.tool()
async def search_images(query: str, size: Optional[str] = None, type_image: Optional[str] = None, layout: Optional[str] = None, license_image: Optional[str] = None, max_results: int = 100000) -> List[Any]: 
    """SEARCHES images. [ACTION]
    
    [RAG Context]
    Search for images with filters (size, type, layout).
    Returns list of images.
    """
    return await media_ops.search_images(query, size, type_image, layout, license_image, max_results)

@mcp.tool()
async def find_clipart(query: str, max_results: int = 100000) -> List[Any]: 
    """SEARCHES clipart. [ACTION]
    
    [RAG Context]
    Search for clipart images.
    Returns list of images.
    """
    return await media_ops.find_clipart(query, max_results)

@mcp.tool()
async def find_gifs(query: str, max_results: int = 100000) -> List[Any]: 
    """SEARCHES GIFs. [ACTION]
    
    [RAG Context]
    Search for animated GIFs.
    Returns list of images.
    """
    return await media_ops.find_gifs(query, max_results)

@mcp.tool()
async def find_transparent(query: str, max_results: int = 100000) -> List[Any]: 
    """SEARCHES transparent. [ACTION]
    
    [RAG Context]
    Search for images with transparent background.
    Returns list of images.
    """
    return await media_ops.find_transparent(query, max_results)

@mcp.tool()
async def find_wallpapers(query: str, max_results: int = 100000) -> List[Any]: 
    """SEARCHES wallpapers. [ACTION]
    
    [RAG Context]
    Search for wallpaper-sized images.
    Returns list of images.
    """
    return await media_ops.find_wallpapers(query, max_results)

@mcp.tool()
async def find_creative_commons(query: str, max_results: int = 100000) -> List[Any]: 
    """SEARCHES CC images. [ACTION]
    
    [RAG Context]
    Search for images with Creative Commons license.
    Returns list of images.
    """
    return await media_ops.find_creative_commons(query, max_results)

@mcp.tool()
async def find_people_images(query: str, max_results: int = 100000) -> List[Any]: 
    """SEARCHES people. [ACTION]
    
    [RAG Context]
    Search for images of people.
    Returns list of images.
    """
    return await media_ops.find_people_images(query, max_results)

@mcp.tool()
async def find_icons(query: str, max_results: int = 100000) -> List[Any]: 
    """SEARCHES icons. [ACTION]
    
    [RAG Context]
    Search for icon images.
    Returns list of images.
    """
    return await media_ops.find_icons(query, max_results)

@mcp.tool()
async def find_red_images(query: str, max_results: int = 100000) -> List[Any]: 
    """SEARCHES red images. [ACTION]
    
    [RAG Context]
    Search for predominantly red images.
    Returns list of images.
    """
    return await media_ops.find_red_images(query, max_results)

@mcp.tool()
async def find_blue_images(query: str, max_results: int = 100000) -> List[Any]: 
    """SEARCHES blue images. [ACTION]
    
    [RAG Context]
    Search for predominantly blue images.
    Returns list of images.
    """
    return await media_ops.find_blue_images(query, max_results)

# ==========================================
# 3. Video Search
# ==========================================
# ==========================================
# 3. Video Search
# ==========================================
@mcp.tool()
async def search_videos(query: str, resolution: Optional[str] = None, duration: Optional[str] = None, max_results: int = 100000) -> List[Any]: 
    """SEARCHES videos. [ACTION]
    
    [RAG Context]
    Search for videos with filters (resolution, duration).
    Returns list of videos.
    """
    return await media_ops.search_videos(query, resolution, duration, max_results)

@mcp.tool()
async def find_short_videos(query: str, max_results: int = 100000) -> List[Any]: 
    """SEARCHES short videos. [ACTION]
    
    [RAG Context]
    Search for short videos (< 5 mins).
    Returns list of videos.
    """
    return await media_ops.find_short_videos(query, max_results)

@mcp.tool()
async def find_long_videos(query: str, max_results: int = 100000) -> List[Any]: 
    """SEARCHES long videos. [ACTION]
    
    [RAG Context]
    Search for long videos (> 20 mins).
    Returns list of videos.
    """
    return await media_ops.find_long_videos(query, max_results)

@mcp.tool()
async def find_high_res_videos(query: str, max_results: int = 100000) -> List[Any]: 
    """SEARCHES HD videos. [ACTION]
    
    [RAG Context]
    Search for high resolution videos.
    Returns list of videos.
    """
    return await media_ops.find_high_res_videos(query, max_results)

@mcp.tool()
async def find_cc_videos(query: str, max_results: int = 100000) -> List[Any]: 
    """SEARCHES CC videos. [ACTION]
    
    [RAG Context]
    Search for videos with Creative Commons license.
    Returns list of videos.
    """
    return await media_ops.find_cc_videos(query, max_results)

# ==========================================
# 4. News
# ==========================================
@mcp.tool()
async def search_news(query: str, region: str = "wt-wt", max_results: int = 100000) -> List[Any]: 
    """SEARCHES news. [ACTION]
    
    [RAG Context]
    Search for news articles.
    Returns list of articles.
    """
    return await news_ops.search_news(query, region, max_results)

@mcp.tool()
async def search_news_topic(topic: str, max_results: int = 100000) -> List[Any]: 
    """SEARCHES topic. [ACTION]
    
    [RAG Context]
    Search news for a specific topic.
    Returns list of articles.
    """
    return await news_ops.search_news_topic(topic, max_results)

@mcp.tool()
async def latest_news(query: str, max_results: int = 100000) -> List[Any]: 
    """SEARCHES latest news. [ACTION]
    
    [RAG Context]
    Get the latest news for a query.
    Returns list of articles.
    """
    return await news_ops.latest_news(query, max_results)

@mcp.tool()
async def get_trending(max_results: int = 100000) -> List[Any]: 
    """FETCHES trending. [ACTION]
    
    [RAG Context]
    Get trending news/searches.
    Returns list of trends.
    """
    return await news_ops.get_trending(max_results)

# ==========================================
# 5. Maps
# ==========================================
@mcp.tool()
async def search_places(query: str, max_results: int = 100000) -> List[Any]: 
    """SEARCHES places. [ACTION]
    
    [RAG Context]
    Search for places/locations.
    Returns list of places.
    """
    return await map_ops.search_places(query, max_results)

@mcp.tool()
async def get_address(query: str) -> List[Any]: 
    """FETCHES address. [ACTION]
    
    [RAG Context]
    Get address details for a query.
    Returns address info.
    """
    return await map_ops.get_address(query)

@mcp.tool()
async def find_near_me(query: str, max_results: int = 100000) -> List[Any]: 
    """SEARCHES nearby. [ACTION]
    
    [RAG Context]
    Search for places near the current location (if inferred).
    Returns list of places.
    """
    return await map_ops.find_near_me(query, max_results)

# ==========================================
# 6. AI & Utilities
# ==========================================
# ==========================================
# 6. AI & Utilities
# ==========================================
@mcp.tool()
async def translate_text(text: str, to_lang: str = "en") -> List[Any]: 
    """TRANSLATES text. [ACTION]
    
    [RAG Context]
    Translate text found in search results.
    Returns translation.
    """
    return await ai_ops.translate_text(text, to_lang)

@mcp.tool()
async def identify_language(text: str) -> str: 
    """IDENTIFIES language. [ACTION]
    
    [RAG Context]
    Identify language of text.
    Returns language code/name.
    """
    return await ai_ops.identify_language(text)

# ==========================================
# 7. Bulk
# ==========================================
@mcp.tool()
async def bulk_text_search(queries: List[str], max_results: int = 100000) -> Dict[str, List[Any]]: 
    """BULK: Text Search. [ACTION]
    
    [RAG Context]
    Perform multiple text searches in parallel.
    Returns dict of results by query.
    """
    return await bulk_ops.bulk_text_search(queries, max_results)

@mcp.tool()
async def bulk_image_search(queries: List[str], max_results: int = 100000) -> Dict[str, List[Any]]: 
    """BULK: Image Search. [ACTION]
    
    [RAG Context]
    Perform multiple image searches in parallel.
    Returns dict of results by query.
    """
    return await bulk_ops.bulk_image_search(queries, max_results)

@mcp.tool()
async def bulk_news_search(queries: List[str], max_results: int = 100000) -> Dict[str, List[Any]]: 
    """BULK: News Search. [ACTION]
    
    [RAG Context]
    Perform multiple news searches in parallel.
    Returns dict of results by query.
    """
    return await bulk_ops.bulk_news_search(queries, max_results)


if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class DdgSearchServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []
