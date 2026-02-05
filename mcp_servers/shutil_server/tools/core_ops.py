import shutil
import os
import structlog
from pathlib import Path
from typing import Dict, Any, Union, Optional

logger = structlog.get_logger()

def validate_path(path: str) -> bool:
    """Check if path exists or parent exists."""
    p = Path(path)
    return p.exists() or p.parent.exists()

def get_disk_usage(path: str) -> Dict[str, Any]:
    """Return total, used, free space."""
    try:
        total, used, free = shutil.disk_usage(path)
        return {
            "total_bytes": total,
            "used_bytes": used,
            "free_bytes": free,
            "total_gb": round(total / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2)
        }
    except Exception as e:
        return {"error": str(e)}

def which_command(cmd: str) -> Optional[str]:
    """Locate a command line executable (shutil.which)."""
    return shutil.which(cmd)

def get_owner_info(path: str) -> Dict[str, Any]:
    """Get user/group info for a file (Using os.stat, related to chown)."""
    try:
        st = os.stat(path)
        return {
            "uid": st.st_uid,
            "gid": st.st_gid
        }
    except Exception as e:
        return {"error": str(e)}

def check_permissions(path: str) -> Dict[str, bool]:
    """Check if file is readable/writable/executable."""
    return {
        "readable": os.access(path, os.R_OK),
        "writable": os.access(path, os.W_OK),
        "executable": os.access(path, os.X_OK)
    }
