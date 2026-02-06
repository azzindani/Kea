
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

from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from tools import (
    text_ops, media_ops, news_ops, map_ops, ai_ops, bulk_ops
)
import structlog
from typing import List, Dict, Any, Optional

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("ddg_search_server", dependencies=["duckduckgo_search"])

# ==========================================
# 1. Text Search
# ==========================================
@mcp.tool()
async def search_text(query: str, region: str = "wt-wt", safe_search: str = "moderate", time: Optional[str] = None, max_results: int = 100000) -> List[Any]: return await text_ops.search_text(query, region, safe_search, time, max_results)
@mcp.tool()
async def search_private(query: str, max_results: int = 100000) -> List[Any]: return await text_ops.search_private(query, max_results)
@mcp.tool()
async def search_answers(query: str) -> List[Any]: return await text_ops.search_answers(query)
@mcp.tool()
async def search_suggestions(query: str, region: str = "wt-wt") -> List[Any]: return await text_ops.search_suggestions(query, region)
@mcp.tool()
async def search_past_day(query: str, max_results: int = 100000) -> List[Any]: return await text_ops.search_past_day(query, max_results)
@mcp.tool()
async def search_past_week(query: str, max_results: int = 100000) -> List[Any]: return await text_ops.search_past_week(query, max_results)
@mcp.tool()
async def search_past_month(query: str, max_results: int = 100000) -> List[Any]: return await text_ops.search_past_month(query, max_results)
@mcp.tool()
async def search_past_year(query: str, max_results: int = 100000) -> List[Any]: return await text_ops.search_past_year(query, max_results)
@mcp.tool()
async def search_region(query: str, region: str, max_results: int = 100000) -> List[Any]: return await text_ops.search_region(query, region, max_results)
@mcp.tool()
async def search_python_docs(query: str, max_results: int = 100000) -> List[Any]: return await text_ops.search_python_docs(query, max_results)
@mcp.tool()
async def search_stackoverflow(query: str, max_results: int = 100000) -> List[Any]: return await text_ops.search_stackoverflow(query, max_results)

# ==========================================
# 2. Image Search
# ==========================================
@mcp.tool()
async def search_images(query: str, size: Optional[str] = None, type_image: Optional[str] = None, layout: Optional[str] = None, license_image: Optional[str] = None, max_results: int = 100000) -> List[Any]: return await media_ops.search_images(query, size, type_image, layout, license_image, max_results)
@mcp.tool()
async def find_clipart(query: str, max_results: int = 100000) -> List[Any]: return await media_ops.find_clipart(query, max_results)
@mcp.tool()
async def find_gifs(query: str, max_results: int = 100000) -> List[Any]: return await media_ops.find_gifs(query, max_results)
@mcp.tool()
async def find_transparent(query: str, max_results: int = 100000) -> List[Any]: return await media_ops.find_transparent(query, max_results)
@mcp.tool()
async def find_wallpapers(query: str, max_results: int = 100000) -> List[Any]: return await media_ops.find_wallpapers(query, max_results)
@mcp.tool()
async def find_creative_commons(query: str, max_results: int = 100000) -> List[Any]: return await media_ops.find_creative_commons(query, max_results)
@mcp.tool()
async def find_people_images(query: str, max_results: int = 100000) -> List[Any]: return await media_ops.find_people_images(query, max_results)
@mcp.tool()
async def find_icons(query: str, max_results: int = 100000) -> List[Any]: return await media_ops.find_icons(query, max_results)
@mcp.tool()
async def find_red_images(query: str, max_results: int = 100000) -> List[Any]: return await media_ops.find_red_images(query, max_results)
@mcp.tool()
async def find_blue_images(query: str, max_results: int = 100000) -> List[Any]: return await media_ops.find_blue_images(query, max_results)

# ==========================================
# 3. Video Search
# ==========================================
@mcp.tool()
async def search_videos(query: str, resolution: Optional[str] = None, duration: Optional[str] = None, max_results: int = 100000) -> List[Any]: return await media_ops.search_videos(query, resolution, duration, max_results)
@mcp.tool()
async def find_short_videos(query: str, max_results: int = 100000) -> List[Any]: return await media_ops.find_short_videos(query, max_results)
@mcp.tool()
async def find_long_videos(query: str, max_results: int = 100000) -> List[Any]: return await media_ops.find_long_videos(query, max_results)
@mcp.tool()
async def find_high_res_videos(query: str, max_results: int = 100000) -> List[Any]: return await media_ops.find_high_res_videos(query, max_results)
@mcp.tool()
async def find_cc_videos(query: str, max_results: int = 100000) -> List[Any]: return await media_ops.find_cc_videos(query, max_results)

# ==========================================
# 4. News
# ==========================================
@mcp.tool()
async def search_news(query: str, region: str = "wt-wt", max_results: int = 100000) -> List[Any]: return await news_ops.search_news(query, region, max_results)
@mcp.tool()
async def search_news_topic(topic: str, max_results: int = 100000) -> List[Any]: return await news_ops.search_news_topic(topic, max_results)
@mcp.tool()
async def latest_news(query: str, max_results: int = 100000) -> List[Any]: return await news_ops.latest_news(query, max_results)
@mcp.tool()
async def get_trending(max_results: int = 100000) -> List[Any]: return await news_ops.get_trending(max_results)

# ==========================================
# 5. Maps
# ==========================================
@mcp.tool()
async def search_places(query: str, max_results: int = 100000) -> List[Any]: return await map_ops.search_places(query, max_results)
@mcp.tool()
async def get_address(query: str) -> List[Any]: return await map_ops.get_address(query)
@mcp.tool()
async def find_near_me(query: str, max_results: int = 100000) -> List[Any]: return await map_ops.find_near_me(query, max_results)

# ==========================================
# 6. AI & Utilities
# ==========================================
@mcp.tool()
async def translate_text(text: str, to_lang: str = "en") -> List[Any]: return await ai_ops.translate_text(text, to_lang)
@mcp.tool()
async def identify_language(text: str) -> str: return await ai_ops.identify_language(text)

# ==========================================
# 7. Bulk
# ==========================================
@mcp.tool()
async def bulk_text_search(queries: List[str], max_results: int = 100000) -> Dict[str, List[Any]]: return await bulk_ops.bulk_text_search(queries, max_results)
@mcp.tool()
async def bulk_image_search(queries: List[str], max_results: int = 100000) -> Dict[str, List[Any]]: return await bulk_ops.bulk_image_search(queries, max_results)
@mcp.tool()
async def bulk_news_search(queries: List[str], max_results: int = 100000) -> Dict[str, List[Any]]: return await bulk_ops.bulk_news_search(queries, max_results)


if __name__ == "__main__":
    mcp.run()