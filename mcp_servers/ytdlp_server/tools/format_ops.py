import yt_dlp
from typing import List, Dict, Any, Optional
from mcp_servers.ytdlp_server.tools import core_ops

def _get_formats(url: str) -> List[Dict[str, Any]]:
    opts = core_ops.get_default_options()
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info.get("formats", [])

def list_formats(url: str) -> List[Dict[str, Any]]:
    """JSON list of all available formats."""
    formats = _get_formats(url)
    # Simplify output
    return [
        {
            "format_id": f.get("format_id"),
            "ext": f.get("ext"),
            "resolution": f.get("resolution"),
            "filesize": f.get("filesize"),
            "note": f.get("format_note"),
            "vcodec": f.get("vcodec"),
            "acodec": f.get("acodec")
        } for f in formats
    ]

def get_best_video_format(url: str) -> Dict[str, Any]:
    """Info on best video stream."""
    formats = _get_formats(url)
    # yt-dlp sorts formats best last usually
    return formats[-1] if formats else {}

def get_best_audio_format(url: str) -> Dict[str, Any]:
    """Info on best audio stream."""
    formats = _get_formats(url)
    audio_only = [f for f in formats if f.get("vcodec") == "none"]
    return audio_only[-1] if audio_only else {}

def get_worst_quality_format(url: str) -> Dict[str, Any]:
    """Smallest file size format."""
    formats = _get_formats(url)
    return formats[0] if formats else {}

def filter_formats_by_res(url: str, height: int) -> List[Dict[str, Any]]:
    """Get formats matching specific height (e.g. 1080)."""
    formats = list_formats(url)
    return [f for f in formats if f.get("resolution") and str(height) in f.get("resolution")]

def filter_formats_by_ext(url: str, ext: str) -> List[Dict[str, Any]]:
    """Get formats by extension (mp4, webm)."""
    formats = list_formats(url)
    return [f for f in formats if f.get("ext") == ext]

def check_format_availability(url: str, format_id: str) -> bool:
    """Does a specific format ID exist?"""
    formats = _get_formats(url)
    return any(f.get("format_id") == format_id for f in formats)
