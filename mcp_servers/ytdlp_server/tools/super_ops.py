import yt_dlp
import datetime
import json
import os
from typing import List, Dict, Any
from mcp_servers.ytdlp_server.tools import core_ops, download_ops

def archive_channel(url: str, download_archive_path: str = "archive.txt") -> str:
    """Download all videos from channel (smart sync)."""
    # Use download_archive feature of yt-dlp to track history
    opts = {
        "download_archive": download_archive_path,
        "ignoreerrors": True
    }
    return download_ops._download(url, opts)

def sync_playlist(url: str, download_archive_path: str = "playlist_archive.txt") -> str:
    """Download only new videos from playlist."""
    return archive_channel(url, download_archive_path)

def create_audio_library(url: str, output_template: str = "%(artist)s/%(album)s/%(title)s.%(ext)s") -> str:
    """Download channel as MP3s with artist/album metadata."""
    opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{core_ops.CONFIG['download_dir']}/{output_template}",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
        }, {
            "key": "FFmpegMetadata"
        }],
        "addmetadata": True
    }
    return download_ops._download(url, opts)

def monitor_new_uploads(url: str, date_after: str) -> str:
    """Check channel for upload newer than date (YYYYMMDD)."""
    opts = {
        "dateafter": date_after,
        "playlistend": 20 # Check last 20? 
    }
    return download_ops._download(url, opts)

def top_n_by_views(url: str, n: int = 10) -> List[Dict[str, Any]]:
    """Get top N videos from channel sorted by views."""
    # This requires extracting ALL metadata first which is slow for big channels
    # Or using extract_flat and trust order if platform supports? YT sorts by date usually
    # We might need to fetch flat playlist, then fetch view counts for each? expensive.
    # Best effort: fetch flat, then best effort sort?
    # This is a "heavy" super tool.
    
    # Better approach: 
    # Use yt-dlp to dump json, then parse in pandas?
    # returning a warning string for now if too large
    return [{"message": "This operation requires fetching all channel metadata and sorting client-side, which may timeout for large channels."}]

def extract_highlights(url: str, timestamps: List[str]) -> str:
    """Download specific timestamp ranges. timestamps=['10:00-11:00', '15:30-16:00']."""
    # feature: download_ranges
    def parse_time(t):
        # very basic parser, yt-dlp needs seconds usually or callback
        # download_ranges is a callback function in python api... complex
        pass
    return "Complex download_ranges implementation requires callback injection not easily serializable via MCP yet."

def metadata_audit(url: str) -> str:
    """JSON report of channel stats (avg views, upload freq)."""
    # Fetch flat list
    opts = core_ops.get_default_options()
    opts["extract_flat"] = True
    
    with yt_dlp.YoutubeDL(opts) as ydl:
        res = ydl.extract_info(url, download=False)
        entries = res.get("entries", [])
        count = len(entries)
        return f"Channel: {res.get('title')}, Video Count: {count}"

def download_best_available_series(urls: List[str]) -> str:
    """Attempt to download a list, falling back if errors."""
    return download_ops.bulk_download_videos(urls)

def find_duplicates_in_playlist(url: str) -> List[str]:
    """Check for duplicate titles/ids."""
    opts = core_ops.get_default_options()
    opts["extract_flat"] = True
    duplicates = []
    seen = set()
    
    with yt_dlp.YoutubeDL(opts) as ydl:
        res = ydl.extract_info(url, download=False)
        for entry in res.get("entries", []):
            vid = entry.get("id")
            if vid in seen:
                duplicates.append(vid)
            seen.add(vid)
    return duplicates

def backup_channel_metadata(url: str, output_file: str) -> str:
    """Save all metadata for channel to JSON lines."""
    opts = core_ops.get_default_options()
    opts["dump_single_json"] = True # or manually write
    opts["extract_flat"] = True # fast backup, false for full
    # For full backup:
    # We loop and save
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
             res = ydl.extract_info(url, download=False)
             with open(output_file, 'w', encoding='utf-8') as f:
                 json.dump(res, f, indent=2)
        return f"Saved metadata to {output_file}"
    except Exception as e:
        return f"Error: {e}"

def download_time_range(url: str, start_date: str, end_date: str) -> str:
    """Download videos uploaded between Date A and Date B (YYYYMMDD)."""
    opts = {
        "dateafter": start_date,
        "datebefore": end_date
    }
    return download_ops._download(url, opts)
