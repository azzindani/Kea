import ffmpeg
import shutil
import os
import structlog
from typing import Dict, Any, Optional

logger = structlog.get_logger()

# Global config
CONFIG = {
    "output_dir": "outputs"
}

def check_ffmpeg_available() -> bool:
    """Verify ffmpeg is in PATH."""
    return shutil.which("ffmpeg") is not None

def get_ffmpeg_version() -> str:
    """Return ffmpeg version."""
    if not check_ffmpeg_available():
        return "Error: ffmpeg not found in PATH."
    try:
        # ffmpeg-python doesn't expose version directly cleanly, run cmd
        import subprocess
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        return result.stdout.splitlines()[0]
    except Exception as e:
        return f"Error: {e}"

def set_output_dir(path: str) -> str:
    """Set default download/output path."""
    if not os.path.exists(path):
        os.makedirs(path)
    CONFIG["output_dir"] = path
    return f"Output directory set to {path}"

def validate_media_file(path: str) -> Dict[str, Any]:
    """Check if file exists and seems readable."""
    if not os.path.exists(path):
        return {"valid": False, "error": "File not found"}
    
    # Try probing
    try:
        ffmpeg.probe(path)
        return {"valid": True, "message": "File is readable by ffmpeg"}
    except ffmpeg.Error as e:
        return {"valid": False, "error": str(e.stderr)}
    except Exception as e:
        return {"valid": False, "error": str(e)}

def get_codecs() -> str:
    """List available codecs (summary)."""
    # ffmpeg -codecs
    if not check_ffmpeg_available(): return "ffmpeg not found"
    import subprocess
    res = subprocess.run(["ffmpeg", "-codecs"], capture_output=True, text=True)
    return res.stdout # Return full string, let user parse or read
