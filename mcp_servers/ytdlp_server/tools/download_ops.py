import yt_dlp
import os
from typing import Dict, Any, List, Optional
from mcp_servers.ytdlp_server.tools import core_ops

def _download(url: str, extra_opts: Dict[str, Any] = None) -> str:
    """Helper to download."""
    opts = core_ops.get_default_options()
    if extra_opts:
        opts.update(extra_opts)
    
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        return "Download started/completed (check output dir)."
    except Exception as e:
        return f"Error: {e}"

def download_video(url: str) -> str:
    """Best quality video+audio."""
    return _download(url)

def download_audio_only(url: str, format: str = "mp3") -> str:
    """Convert to mp3/m4a."""
    opts = {
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": format,
            "preferredquality": "192",
        }],
    }
    return _download(url, opts)

def download_specific_format(url: str, format_id: str) -> str:
    """Download by format ID."""
    return _download(url, {"format": format_id})

def download_thumbnail(url: str) -> str:
    """Save thumbnail file."""
    # skip_download=True, writethumbnail=True
    opts = {
        "skip_download": True,
        "writethumbnail": True
    }
    return _download(url, opts)

def download_subtitles(url: str, lang: str = "en") -> str:
    """Save .vtt/.srt files."""
    opts = {
        "skip_download": True,
        "writesubtitles": True,
        "subtitleslangs": [lang]
    }
    return _download(url, opts)

def download_description(url: str) -> str:
    """Save .description file."""
    opts = {
        "skip_download": True,
        "writedescription": True
    }
    return _download(url, opts)

def download_video_restricted(url: str, max_height: int = 1080) -> str:
    """Download with resolution limit (save bandwidth)."""
    # format selection syntax: bestvideo[height<=1080]+bestaudio/best[height<=1080]
    f_str = f"bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]"
    return _download(url, {"format": f_str})

def download_playlist_indices(url: str, indices: str) -> str:
    """Download specific items (e.g., '1,3-5')."""
    return _download(url, {"playlist_items": indices})

def download_channel_latest(url: str, n: int = 5) -> str:
    """Download latest N videos."""
    return _download(url, {"playlistend": n})

def download_with_metadata(url: str) -> str:
    """Embed metadata/chapters into file."""
    opts = {
        "addmetadata": True,
        "writethumbnail": True # Embed thumb usually requires writing it first or parsing
    }
    return _download(url, opts)
