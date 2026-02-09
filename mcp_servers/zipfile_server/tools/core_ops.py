import zipfile
import os
import structlog
from typing import Dict, Any

logger = structlog.get_logger()

def is_zipfile(path: str, **kwargs) -> bool:
    """Check if a file is a valid ZIP file."""
    if not os.path.exists(path): return False
    return zipfile.is_zipfile(path)

def validate_archive(path: str, **kwargs) -> Dict[str, Any]:
    """Detailed integrity check using zipfile.testzip()."""
    if not is_zipfile(path):
        return {"valid": False, "error": "Not a zip file or does not exist."}
    
    try:
        with zipfile.ZipFile(path, 'r') as zf:
            bad_file = zf.testzip()
            if bad_file:
                return {"valid": False, "error": f"Corrupt file found: {bad_file}"}
            else:
                return {"valid": True, "message": "Archive integrity verified."}
    except Exception as e:
        return {"valid": False, "error": str(e)}

def get_zip_comment(path: str, **kwargs) -> str:
    """Return the global comment of the archive."""
    try:
        with zipfile.ZipFile(path, 'r') as zf:
            return zf.comment.decode('utf-8', errors='replace')
    except Exception as e:
        return f"Error: {e}"

def set_zip_comment(path: str, comment: str, **kwargs) -> str:
    """Update the archive comment (requires rewrite usually, but zipfile supports mode 'a')."""
    try:
        with zipfile.ZipFile(path, 'a') as zf:
            zf.comment = comment.encode('utf-8')
        return "Comment updated."
    except Exception as e:
        return f"Error: {e}"

def get_compression_type(path: str, **kwargs) -> Dict[str, str]:
    """Check defaults (stored, deflated, bzip2, lzma)."""
    # Check first file or default
    try:
        with zipfile.ZipFile(path, 'r') as zf:
            algo_map = {
                zipfile.ZIP_STORED: "STORED",
                zipfile.ZIP_DEFLATED: "DEFLATED",
                zipfile.ZIP_BZIP2: "BZIP2",
                zipfile.ZIP_LZMA: "LZMA"
            }
            # Scan all to see mix? Just return general info
            infos = zf.infolist()
            if not infos: return {"type": "empty"}
            
            # Count methods
            methods = {}
            for inf in infos:
                name = algo_map.get(inf.compress_type, str(inf.compress_type))
                methods[name] = methods.get(name, 0) + 1
            return {"compression_methods_distribution": methods}
    except Exception as e:
        return {"error": str(e)}

def check_integrity(path: str, **kwargs) -> Dict[str, Any]:
    """Alias for validate_archive."""
    return validate_archive(path, **kwargs)
