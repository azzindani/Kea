# /// script
# dependencies = [
#   "mcp",
#   "pandas",
#   "structlog",
#   "yt-dlp",
# ]
# ///

from mcp.server.fastmcp import FastMCP
from tools import (
    core_ops, info_ops, format_ops, download_ops, bulk_ops, super_ops
)
import structlog
from typing import Dict, Any, Optional, List, Tuple

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("ytdlp_server", dependencies=["pandas", "yt-dlp"])

# ==========================================
# 1. Core
# ==========================================
@mcp.tool()
def get_version() -> str: return core_ops.get_version()
@mcp.tool()
def update_binary() -> str: return core_ops.update_binary()
@mcp.tool()
def set_download_dir(path: str) -> str: return core_ops.set_download_dir(path)
@mcp.tool()
def set_cookies_file(path: str) -> str: return core_ops.set_cookies_file(path)
@mcp.tool()
def set_proxy(url: str) -> str: return core_ops.set_proxy(url)
@mcp.tool()
def set_user_agent(ua: str) -> str: return core_ops.set_user_agent(ua)
@mcp.tool()
def get_default_options() -> Dict[str, Any]: return core_ops.get_default_options()

# ==========================================
# 2. Info Extraction
# ==========================================
@mcp.tool()
def get_video_info(url: str) -> Dict[str, Any]: return info_ops.get_video_info(url)
@mcp.tool()
def get_video_title(url: str) -> str: return info_ops.get_video_title(url)
@mcp.tool()
def get_video_description(url: str) -> str: return info_ops.get_video_description(url)
@mcp.tool()
def get_video_tags(url: str) -> List[str]: return info_ops.get_video_tags(url)
@mcp.tool()
def get_video_thumbnail_url(url: str) -> str: return info_ops.get_video_thumbnail_url(url)
@mcp.tool()
def get_playlist_info(url: str, max_items: int = 50) -> Dict[str, Any]: return info_ops.get_playlist_info(url, max_items)
@mcp.tool()
def get_channel_info(url: str, max_items: int = 10) -> Dict[str, Any]: return info_ops.get_channel_info(url, max_items)
@mcp.tool()
def search_videos(query: str, n: int = 5) -> List[Dict[str, Any]]: return info_ops.search_videos(query, n)
@mcp.tool()
def get_subtitles_list(url: str) -> Dict[str, Any]: return info_ops.get_subtitles_list(url)
@mcp.tool()
def get_view_count(url: str) -> int: return info_ops.get_view_count(url)
@mcp.tool()
def get_duration(url: str) -> int: return info_ops.get_duration(url)

# ==========================================
# 3. Format Operations
# ==========================================
@mcp.tool()
def list_formats(url: str) -> List[Dict[str, Any]]: return format_ops.list_formats(url)
@mcp.tool()
def get_best_video_format(url: str) -> Dict[str, Any]: return format_ops.get_best_video_format(url)
@mcp.tool()
def get_best_audio_format(url: str) -> Dict[str, Any]: return format_ops.get_best_audio_format(url)
@mcp.tool()
def get_worst_quality_format(url: str) -> Dict[str, Any]: return format_ops.get_worst_quality_format(url)
@mcp.tool()
def filter_formats_by_res(url: str, height: int) -> List[Dict[str, Any]]: return format_ops.filter_formats_by_res(url, height)
@mcp.tool()
def check_format_availability(url: str, format_id: str) -> bool: return format_ops.check_format_availability(url, format_id)

# ==========================================
# 4. Download Operations
# ==========================================
@mcp.tool()
def download_video(url: str) -> str: return download_ops.download_video(url)
@mcp.tool()
def download_audio_only(url: str, format: str = "mp3") -> str: return download_ops.download_audio_only(url, format)
@mcp.tool()
def download_specific_format(url: str, format_id: str) -> str: return download_ops.download_specific_format(url, format_id)
@mcp.tool()
def download_thumbnail(url: str) -> str: return download_ops.download_thumbnail(url)
@mcp.tool()
def download_subtitles(url: str, lang: str = "en") -> str: return download_ops.download_subtitles(url, lang)
@mcp.tool()
def download_description(url: str) -> str: return download_ops.download_description(url)
@mcp.tool()
def download_video_restricted(url: str, max_height: int = 1080) -> str: return download_ops.download_video_restricted(url, max_height)
@mcp.tool()
def download_playlist_indices(url: str, indices: str) -> str: return download_ops.download_playlist_indices(url, indices)
@mcp.tool()
def download_channel_latest(url: str, n: int = 5) -> str: return download_ops.download_channel_latest(url, n)
@mcp.tool()
def download_with_metadata(url: str) -> str: return download_ops.download_with_metadata(url)

# ==========================================
# 5. Bulk Operations
# ==========================================
@mcp.tool()
def bulk_get_info(urls: List[str]) -> Dict[str, Any]: return bulk_ops.bulk_get_info(urls)
@mcp.tool()
def bulk_download_videos(urls: List[str]) -> str: return bulk_ops.bulk_download_videos(urls)
@mcp.tool()
def bulk_download_audio(urls: List[str]) -> str: return bulk_ops.bulk_download_audio(urls)
@mcp.tool()
def verify_links(urls: List[str]) -> Dict[str, bool]: return bulk_ops.verify_links(urls)
@mcp.tool()
def get_common_metadata_bulk(urls: List[str]) -> List[Dict[str, Any]]: return bulk_ops.get_common_metadata_bulk(urls)
@mcp.tool()
def bulk_search_and_download(queries: List[str]) -> str: return bulk_ops.bulk_search_and_download(queries)

# ==========================================
# 6. Super Tools
# ==========================================
@mcp.tool()
def archive_channel(url: str, download_archive_path: str = "archive.txt") -> str: return super_ops.archive_channel(url, download_archive_path)
@mcp.tool()
def sync_playlist(url: str, download_archive_path: str = "playlist_archive.txt") -> str: return super_ops.sync_playlist(url, download_archive_path)
@mcp.tool()
def create_audio_library(url: str, output_template: str = "%(artist)s/%(album)s/%(title)s.%(ext)s") -> str: return super_ops.create_audio_library(url, output_template)
@mcp.tool()
def monitor_new_uploads(url: str, date_after: str) -> str: return super_ops.monitor_new_uploads(url, date_after)
@mcp.tool()
def top_n_by_views(url: str, n: int = 10) -> List[Dict[str, Any]]: return super_ops.top_n_by_views(url, n)
@mcp.tool()
def extract_highlights(url: str, timestamps: List[str]) -> str: return super_ops.extract_highlights(url, timestamps)
@mcp.tool()
def metadata_audit(url: str) -> str: return super_ops.metadata_audit(url)
@mcp.tool()
def download_best_available_series(urls: List[str]) -> str: return super_ops.download_best_available_series(urls)
@mcp.tool()
def find_duplicates_in_playlist(url: str) -> List[str]: return super_ops.find_duplicates_in_playlist(url)
@mcp.tool()
def backup_channel_metadata(url: str, output_file: str) -> str: return super_ops.backup_channel_metadata(url, output_file)
@mcp.tool()
def download_time_range(url: str, start_date: str, end_date: str) -> str: return super_ops.download_time_range(url, start_date, end_date)

if __name__ == "__main__":
    mcp.run()
