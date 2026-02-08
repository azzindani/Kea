
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "mcp",
#   "pandas",
#   "structlog",
#   "yt-dlp",
# ]
# ///

from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.ytdlp_server.tools import (
    core_ops, info_ops, format_ops, download_ops, bulk_ops, super_ops
)
import structlog
from typing import Dict, Any, Optional, List, Tuple

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging import setup_logging
setup_logging()

mcp = FastMCP("ytdlp_server", dependencies=["pandas", "yt-dlp"])

# ==========================================
# 1. Core
# ==========================================
# ==========================================
# 1. Core
# ==========================================
@mcp.tool()
def get_version() -> str: 
    """FETCHES version. [ACTION]
    
    [RAG Context]
    Get installed yt-dlp version.
    Returns version string.
    """
    return core_ops.get_version()

@mcp.tool()
def update_binary() -> str: 
    """UPDATES binary. [ACTION]
    
    [RAG Context]
    Update yt-dlp to latest version.
    Returns status string.
    """
    return core_ops.update_binary()

@mcp.tool()
def set_download_dir(path: str) -> str: 
    """SETS download dir. [ACTION]
    
    [RAG Context]
    Set default directory for downloads.
    Returns status string.
    """
    return core_ops.set_download_dir(path)

@mcp.tool()
def set_cookies_file(path: str) -> str: 
    """SETS cookies. [ACTION]
    
    [RAG Context]
    Set cookies content for auth.
    Returns status string.
    """
    return core_ops.set_cookies_file(path)

@mcp.tool()
def set_proxy(url: str) -> str: 
    """SETS proxy. [ACTION]
    
    [RAG Context]
    Set proxy URL for requests.
    Returns status string.
    """
    return core_ops.set_proxy(url)

@mcp.tool()
def set_user_agent(ua: str) -> str: 
    """SETS user agent. [ACTION]
    
    [RAG Context]
    Set custom User-Agent.
    Returns status string.
    """
    return core_ops.set_user_agent(ua)

@mcp.tool()
def get_default_options() -> Dict[str, Any]: 
    """FETCHES options. [ACTION]
    
    [RAG Context]
    Get current default configuration.
    Returns JSON dict.
    """
    return core_ops.get_default_options()

# ==========================================
# 2. Info Extraction
# ==========================================
@mcp.tool()
def get_video_info(url: str) -> Dict[str, Any]: 
    """FETCHES video info. [ACTION]
    
    [RAG Context]
    Get comprehensive metadata for video.
    Returns JSON dict.
    """
    return info_ops.get_video_info(url)

@mcp.tool()
def get_video_title(url: str) -> str: 
    """FETCHES title. [ACTION]
    
    [RAG Context]
    Get video title.
    Returns string.
    """
    return info_ops.get_video_title(url)

@mcp.tool()
def get_video_description(url: str) -> str: 
    """FETCHES description. [ACTION]
    
    [RAG Context]
    Get video description text.
    Returns string.
    """
    return info_ops.get_video_description(url)

@mcp.tool()
def get_video_tags(url: str) -> List[str]: 
    """FETCHES tags. [ACTION]
    
    [RAG Context]
    Get video tags/keywords.
    Returns list of strings.
    """
    return info_ops.get_video_tags(url)

@mcp.tool()
def get_video_thumbnail_url(url: str) -> str: 
    """FETCHES thumbnail URL. [ACTION]
    
    [RAG Context]
    Get URL of video thumbnail.
    Returns URL string.
    """
    return info_ops.get_video_thumbnail_url(url)

@mcp.tool()
def get_playlist_info(url: str, max_items: int = 50) -> Dict[str, Any]: 
    """FETCHES playlist info. [ACTION]
    
    [RAG Context]
    Get metadata for playlist.
    Returns JSON dict.
    """
    return info_ops.get_playlist_info(url, max_items)

@mcp.tool()
def get_channel_info(url: str, max_items: int = 10) -> Dict[str, Any]: 
    """FETCHES channel info. [ACTION]
    
    [RAG Context]
    Get metadata for channel/user.
    Returns JSON dict.
    """
    return info_ops.get_channel_info(url, max_items)

@mcp.tool()
def search_videos(query: str, n: int = 5) -> List[Dict[str, Any]]: 
    """SEARCHES videos. [ACTION]
    
    [RAG Context]
    Search YouTube for query.
    Returns list of results.
    """
    return info_ops.search_videos(query, n)

@mcp.tool()
def get_subtitles_list(url: str) -> Dict[str, Any]: 
    """LISTS subtitles. [ACTION]
    
    [RAG Context]
    List available subtitles for video.
    Returns JSON dict.
    """
    return info_ops.get_subtitles_list(url)

@mcp.tool()
def get_view_count(url: str) -> int: 
    """FETCHES view count. [ACTION]
    
    [RAG Context]
    Get number of views.
    Returns integer.
    """
    return info_ops.get_view_count(url)

@mcp.tool()
def get_duration(url: str) -> int: 
    """FETCHES duration. [ACTION]
    
    [RAG Context]
    Get duration in seconds.
    Returns integer.
    """
    return info_ops.get_duration(url)

# ==========================================
# 3. Format Operations
# ==========================================
@mcp.tool()
def list_formats(url: str) -> List[Dict[str, Any]]: 
    """LISTS formats. [ACTION]
    
    [RAG Context]
    List available download formats.
    Returns list of dicts.
    """
    return format_ops.list_formats(url)

@mcp.tool()
def get_best_video_format(url: str) -> Dict[str, Any]: 
    """FETCHES best video. [ACTION]
    
    [RAG Context]
    Get info for best video quality format.
    Returns JSON dict.
    """
    return format_ops.get_best_video_format(url)

@mcp.tool()
def get_best_audio_format(url: str) -> Dict[str, Any]: 
    """FETCHES best audio. [ACTION]
    
    [RAG Context]
    Get info for best audio quality format.
    Returns JSON dict.
    """
    return format_ops.get_best_audio_format(url)

@mcp.tool()
def get_worst_quality_format(url: str) -> Dict[str, Any]: 
    """FETCHES worst. [ACTION]
    
    [RAG Context]
    Get info for lowest quality format (bandwidth saving).
    Returns JSON dict.
    """
    return format_ops.get_worst_quality_format(url)

@mcp.tool()
def filter_formats_by_res(url: str, height: int) -> List[Dict[str, Any]]: 
    """FILTERS formats. [ACTION]
    
    [RAG Context]
    Find formats matching specific resolution (height).
    Returns list of dicts.
    """
    return format_ops.filter_formats_by_res(url, height)

@mcp.tool()
def check_format_availability(url: str, format_id: str) -> bool: 
    """CHECKS format. [ACTION]
    
    [RAG Context]
    Verify if specific format ID exists.
    Returns boolean.
    """
    return format_ops.check_format_availability(url, format_id)

# ==========================================
# 4. Download Operations
# ==========================================
# ==========================================
# 4. Download Operations
# ==========================================
@mcp.tool()
def download_video(url: str) -> str: 
    """DOWNLOADS video. [ACTION]
    
    [RAG Context]
    Download video in best quality.
    Returns output path.
    """
    return download_ops.download_video(url)

@mcp.tool()
def download_audio_only(url: str, format: str = "mp3") -> str: 
    """DOWNLOADS audio. [ACTION]
    
    [RAG Context]
    Download audio track only (mp3/m4a).
    Returns output path.
    """
    return download_ops.download_audio_only(url, format)

@mcp.tool()
def download_specific_format(url: str, format_id: str) -> str: 
    """DOWNLOADS format. [ACTION]
    
    [RAG Context]
    Download specific format by ID.
    Returns output path.
    """
    return download_ops.download_specific_format(url, format_id)

@mcp.tool()
def download_thumbnail(url: str) -> str: 
    """DOWNLOADS thumbnail. [ACTION]
    
    [RAG Context]
    Download video thumbnail image.
    Returns output path.
    """
    return download_ops.download_thumbnail(url)

@mcp.tool()
def download_subtitles(url: str, lang: str = "en") -> str: 
    """DOWNLOADS subtitles. [ACTION]
    
    [RAG Context]
    Download subtitles in specific language.
    Returns output path.
    """
    return download_ops.download_subtitles(url, lang)

@mcp.tool()
def download_description(url: str) -> str: 
    """DOWNLOADS description. [ACTION]
    
    [RAG Context]
    Save video description to file.
    Returns output path.
    """
    return download_ops.download_description(url)

@mcp.tool()
def download_video_restricted(url: str, max_height: int = 1080) -> str: 
    """DOWNLOADS restricted. [ACTION]
    
    [RAG Context]
    Download video capped at max resolution.
    Returns output path.
    """
    return download_ops.download_video_restricted(url, max_height)

@mcp.tool()
def download_playlist_indices(url: str, indices: str) -> str: 
    """DOWNLOADS indices. [ACTION]
    
    [RAG Context]
    Download specific items from playlist (e.g., "1,2,5-10").
    Returns report string.
    """
    return download_ops.download_playlist_indices(url, indices)

@mcp.tool()
def download_channel_latest(url: str, n: int = 5) -> str: 
    """DOWNLOADS latest. [ACTION]
    
    [RAG Context]
    Download most recent N videos from channel.
    Returns report string.
    """
    return download_ops.download_channel_latest(url, n)

@mcp.tool()
def download_with_metadata(url: str) -> str: 
    """DOWNLOADS metadata. [ACTION]
    
    [RAG Context]
    Download video with full metadata embedded.
    Returns output path.
    """
    return download_ops.download_with_metadata(url)

# ==========================================
# 5. Bulk Operations
# ==========================================
@mcp.tool()
def bulk_get_info(urls: List[str]) -> Dict[str, Any]: 
    """BULK: Get Info. [ACTION]
    
    [RAG Context]
    Get metadata for multiple URLs.
    Returns dict of url->info.
    """
    return bulk_ops.bulk_get_info(urls)

@mcp.tool()
def bulk_download_videos(urls: List[str]) -> str: 
    """BULK: Download Videos. [ACTION]
    
    [RAG Context]
    Download multiple videos.
    Returns report string.
    """
    return bulk_ops.bulk_download_videos(urls)

@mcp.tool()
def bulk_download_audio(urls: List[str]) -> str: 
    """BULK: Download Audio. [ACTION]
    
    [RAG Context]
    Download audio from multiple URLs.
    Returns report string.
    """
    return bulk_ops.bulk_download_audio(urls)

@mcp.tool()
def verify_links(urls: List[str]) -> Dict[str, bool]: 
    """VERIFIES links. [ACTION]
    
    [RAG Context]
    Check if multiple URLs are valid/accessible.
    Returns dict of url->bool.
    """
    return bulk_ops.verify_links(urls)

@mcp.tool()
def get_common_metadata_bulk(urls: List[str]) -> List[Dict[str, Any]]: 
    """FETCHES common metadata. [ACTION]
    
    [RAG Context]
    Get simplified metadata for multiple URLs.
    Returns list of dicts.
    """
    return bulk_ops.get_common_metadata_bulk(urls)

@mcp.tool()
def bulk_search_and_download(queries: List[str]) -> str: 
    """BULK: Search & Download. [ACTION]
    
    [RAG Context]
    Search and download top result for each query.
    Returns report string.
    """
    return bulk_ops.bulk_search_and_download(queries)

# ==========================================
# 6. Super Tools
# ==========================================
@mcp.tool()
def archive_channel(url: str, download_archive_path: str = "archive.txt") -> str: 
    """ARCHIVES channel. [ACTION]
    
    [RAG Context]
    Download entire channel, skipping already downloaded.
    Returns report string.
    """
    return super_ops.archive_channel(url, download_archive_path)

@mcp.tool()
def sync_playlist(url: str, download_archive_path: str = "playlist_archive.txt") -> str: 
    """SYNCS playlist. [ACTION]
    
    [RAG Context]
    Keep local folder in sync with playlist.
    Returns report string.
    """
    return super_ops.sync_playlist(url, download_archive_path)

@mcp.tool()
def create_audio_library(url: str, output_template: str = "%(artist)s/%(album)s/%(title)s.%(ext)s") -> str: 
    """CREATES music lib. [ACTION]
    
    [RAG Context]
    Download and organize audio with metadata.
    Returns report string.
    """
    return super_ops.create_audio_library(url, output_template)

@mcp.tool()
def monitor_new_uploads(url: str, date_after: str) -> str: 
    """MONITORS uploads. [ACTION]
    
    [RAG Context]
    Download videos uploaded after date.
    Returns report string.
    """
    return super_ops.monitor_new_uploads(url, date_after)

@mcp.tool()
def top_n_by_views(url: str, n: int = 10) -> List[Dict[str, Any]]: 
    """FETCHES top views. [ACTION]
    
    [RAG Context]
    Get N most viewed videos from channel.
    Returns list of dicts.
    """
    return super_ops.top_n_by_views(url, n)

@mcp.tool()
def extract_highlights(url: str, timestamps: List[str]) -> str: 
    """EXTRACTS highlights. [ACTION]
    
    [RAG Context]
    Download specific segments (start-end).
    Returns report string.
    """
    return super_ops.extract_highlights(url, timestamps)

@mcp.tool()
def metadata_audit(url: str) -> str: 
    """AUDITS metadata. [ACTION]
    
    [RAG Context]
    Analyze metadata quality/completeness.
    Returns report string.
    """
    return super_ops.metadata_audit(url)

@mcp.tool()
def download_best_available_series(urls: List[str]) -> str: 
    """DOWNLOADS series. [ACTION]
    
    [RAG Context]
    Smart download for series/playlist.
    Returns report string.
    """
    return super_ops.download_best_available_series(urls)

@mcp.tool()
def find_duplicates_in_playlist(url: str) -> List[str]: 
    """FINDS duplicates. [ACTION]
    
    [RAG Context]
    Find duplicate videos in playlist.
    Returns list of titles/IDs.
    """
    return super_ops.find_duplicates_in_playlist(url)

@mcp.tool()
def backup_channel_metadata(url: str, output_file: str) -> str: 
    """BACKUPS metadata. [ACTION]
    
    [RAG Context]
    Save all channel metadata to JSON.
    Returns output path.
    """
    return super_ops.backup_channel_metadata(url, output_file)

@mcp.tool()
def download_time_range(url: str, start_date: str, end_date: str) -> str: 
    """DOWNLOADS timeframe. [ACTION]
    
    [RAG Context]
    Download videos within date range.
    Returns report string.
    """
    return super_ops.download_time_range(url, start_date, end_date)

if __name__ == "__main__":
    mcp.run()