import yt_dlp
from typing import Dict, Any, List, Optional
from mcp_servers.ytdlp_server.tools import core_ops

def _extract(url: str, extra_opts: Dict[str, Any] = None) -> Dict[str, Any]:
    """Helper to extract info with default options."""
    opts = core_ops.get_default_options()
    opts["extract_flat"] = False # Need full info
    if extra_opts:
        opts.update(extra_opts)
    
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)

def get_video_info(url: str) -> Dict[str, Any]:
    """Full JSON metadata for a video."""
    return _extract(url)

def get_video_title(url: str) -> str:
    """Just the title."""
    info = _extract(url)
    return info.get("title", "Unknown")

def get_video_description(url: str) -> str:
    """Just the description."""
    info = _extract(url)
    return info.get("description", "")

def get_video_tags(url: str) -> List[str]:
    """List of tags."""
    info = _extract(url)
    return info.get("tags", [])

def get_video_thumbnail_url(url: str) -> str:
    """Max res thumbnail URL."""
    info = _extract(url)
    return info.get("thumbnail", "")

def get_playlist_info(url: str, max_items: int = 50) -> Dict[str, Any]:
    """Metadata for playlist (list of items, limited)."""
    # extract_flat=True is much faster for playlists
    opts = core_ops.get_default_options()
    opts["extract_flat"] = True
    opts["playlistend"] = max_items
    
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)

def get_channel_info(url: str, max_items: int = 10) -> Dict[str, Any]:
    """Metadata for channel (latest videos)."""
    return get_playlist_info(url, max_items)

def search_videos(query: str, n: int = 5) -> List[Dict[str, Any]]:
    """Search YouTube and return top N results metadata."""
    opts = core_ops.get_default_options()
    opts["extract_flat"] = True
    
    # yt-dlp search syntax: "ytsearchN:query"
    search_query = f"ytsearch{n}:{query}"
    
    with yt_dlp.YoutubeDL(opts) as ydl:
        res = ydl.extract_info(search_query, download=False)
        return res.get("entries", [])

def get_comments(url: str, max_comments: int = 20) -> List[Dict[str, Any]]:
    """Extract top N comments."""
    opts = {"getcomments": True, "playlist_items": f"1-{max_comments}"} # Not exact CLI arg, but controlled via extract
    # comments extraction in API is tricky, usually part of full info if configured
    # enabling check
    # Force full extraction
    info = _extract(url) # This might be slow if comments are huge
    # In newer yt-dlp, comments are separate sometimes
    comments = info.get("comments", [])
    return comments[:max_comments]

def get_subtitles_list(url: str) -> Dict[str, Any]:
    """List available subs (auto & manual)."""
    info = _extract(url)
    return {
        "subtitles": list(info.get("subtitles", {}).keys()),
        "automatic_captions": list(info.get("automatic_captions", {}).keys())
    }

def get_view_count(url: str) -> int:
    """Return view count."""
    info = _extract(url)
    return info.get("view_count", 0)

def get_duration(url: str) -> int:
    """Return duration in seconds."""
    info = _extract(url)
    return info.get("duration", 0)
