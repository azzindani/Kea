import yt_dlp
import os
import structlog
from typing import Dict, Any

logger = structlog.get_logger()

# Global configuration state
CONFIG = {
    "download_dir": "downloads",
    "cookies_file": None,
    "proxy": None,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "noplaylist": True, # Default to single video unless specified
}

def get_version() -> str:
    """Return yt-dlp version."""
    return yt_dlp.version.__version__

def update_binary() -> str:
    """Run update command (simulated for lib mode usually, checking version)."""
    return f"Current version: {get_version()}. To update, run 'pip install -U yt-dlp'."

def set_download_dir(path: str) -> str:
    """Configure default download path."""
    if not os.path.exists(path):
        os.makedirs(path)
    CONFIG["download_dir"] = path
    return f"Download directory set to {path}"

def set_cookies_file(path: str) -> str:
    """Set path to cookies.txt (for auth)."""
    if os.path.exists(path):
        CONFIG["cookies_file"] = path
        return f"Cookies file set to {path}"
    return "Error: Cookies file not found."

def set_proxy(url: str) -> str:
    """Set proxy URL."""
    CONFIG["proxy"] = url
    return f"Proxy set to {url}"

def set_user_agent(ua: str) -> str:
    """Custom UA string."""
    CONFIG["user_agent"] = ua
    return "User Agent updated."

class SilentLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass
    def info(self, msg): pass

def get_default_options() -> Dict[str, Any]:
    """Return current config dict suitable for YoutubeDL."""
    opts = {
        "outtmpl": f"{CONFIG['download_dir']}/%(title)s.%(ext)s",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": CONFIG["noplaylist"],
        "user_agent": CONFIG["user_agent"],
        # Basic error handling
        "ignoreerrors": True,
        # Prevent stdout pollution
        "logger": SilentLogger(),
        # Prevent freeze on existing files or network issues
        "nooverwrites": True,
        "noprogress": True,
        "socket_timeout": 15,
    }
    if CONFIG["cookies_file"]:
        opts["cookiefile"] = CONFIG["cookies_file"]
    if CONFIG["proxy"]:
        opts["proxy"] = CONFIG["proxy"]
        
    return opts

def clear_cache() -> str:
    """Clear internal cache."""
    # yt-dlp handles cache internally, usually deleting cache dir helps
    # We can try to expose the cache dir clean if needed
    return "Cache clearing requires filesystem access to ~/.cache/yt-dlp. Not implemented in memory."
