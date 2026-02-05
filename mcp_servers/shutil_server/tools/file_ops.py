import shutil
import os
from pathlib import Path
from typing import Optional, Union

def copy_file(src: str, dst: str) -> str:
    """Copy data and mode (shutil.copy)."""
    return str(shutil.copy(src, dst))

def copy_file_2(src: str, dst: str) -> str:
    """Copy data and all stat info (shutil.copy2)."""
    return str(shutil.copy2(src, dst))

def copy_mode(src: str, dst: str) -> str:
    """Copy permission bits only (shutil.copymode)."""
    shutil.copymode(src, dst)
    return f"Mode copied from {src} to {dst}"

def copy_stat(src: str, dst: str) -> str:
    """Copy permission bits and other stat info (shutil.copystat)."""
    shutil.copystat(src, dst)
    return f"Stats copied from {src} to {dst}"

def copy_file_content(src: str, dst: str) -> str:
    """Copy data only, no metadata (shutil.copyfile)."""
    return str(shutil.copyfile(src, dst))

def move_file(src: str, dst: str) -> str:
    """Recursive move file (shutil.move)."""
    return str(shutil.move(src, dst))

def change_ownership(path: str, user: Optional[str] = None, group: Optional[str] = None) -> str:
    """Change user and/or group (shutil.chown)."""
    shutil.chown(path, user=user, group=group)
    return f"Ownership changed for {path}"

def touch_file(path: str) -> str:
    """Update timestamps (pathlib)."""
    Path(path).touch()
    return f"Touched {path}"

def rename_file(src: str, dst: str) -> str:
    """Simple rename (os.rename)."""
    os.rename(src, dst)
    return f"Renamed {src} to {dst}"
