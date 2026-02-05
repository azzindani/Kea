import shutil
from typing import List, Tuple, Any

def make_archive(base_name: str, format: str, root_dir: str) -> str:
    """Create an archive (zip, tar, gztar, etc.)."""
    return str(shutil.make_archive(base_name, format, root_dir))

def unpack_archive(filename: str, extract_dir: str, format: str = None) -> str:
    """Extract an archive to a directory."""
    shutil.unpack_archive(filename, extract_dir, format)
    return f"Unpacked {filename} into {extract_dir}"

def get_archive_formats() -> List[Tuple[str, str]]:
    """List supported creation formats."""
    # Returns [(name, description), ...]
    return shutil.get_archive_formats()

def get_unpack_formats() -> List[Tuple[str, List[str], str]]:
    """List supported extraction formats."""
    # Returns [(name, extensions, description), ...]
    return shutil.get_unpack_formats()

def register_archive_format(name: str, function: Any, extra_args: List[Tuple[str, Any]] = None, description: str = "") -> str:
    """Register new format (stub wrapper)."""
    # Complex to pass functions via JSON, likely skipping implementation logic here
    # Just returning info that it exists in shutil
    return "Dynamic registration via MCP not fully supported without code injection."

def unregister_archive_format(name: str) -> str:
    """Remove format."""
    shutil.unregister_archive_format(name)
    return f"Unregistered format {name}"

def compress_directory(dir_path: str, archive_path: str) -> str:
    """Specific alias for directory compression (auto-detects format from ext)."""
    # Infer format
    fmt = "zip"
    if archive_path.endswith(".tar"): fmt = "tar"
    elif archive_path.endswith(".tar.gz") or archive_path.endswith(".tgz"): fmt = "gztar"
    
    # base_name is path without extension for make_archive
    base_name = archive_path.replace(f".{fmt}", "").replace(".tar.gz", "")
    return str(shutil.make_archive(base_name, fmt, dir_path))
