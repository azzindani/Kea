import shutil
import os
from pathlib import Path
from typing import List, Dict, Any

def copy_tree(src: str, dst: str) -> str:
    """Recursively copy entire directory tree (shutil.copytree)."""
    return str(shutil.copytree(src, dst))

def copy_tree_dirs_exist(src: str, dst: str) -> str:
    """Copy tree, allowing existing destination (dirs_exist_ok=True)."""
    return str(shutil.copytree(src, dst, dirs_exist_ok=True))

def remove_tree(path: str) -> str:
    """Recursively delete a directory tree (shutil.rmtree)."""
    shutil.rmtree(path)
    return f"Removed tree {path}"

def remove_tree_safe(path: str) -> str:
    """Rmtree with safety checks (e.g. not root)."""
    p = Path(path).resolve()
    if p.parent == p: # Root check
         return "Error: Cannot delete root directory."
    shutil.rmtree(path)
    return f"Safely removed tree {path}"

def move_directory(src: str, dst: str) -> str:
    """Move directory to new location (shutil.move)."""
    return str(shutil.move(src, dst))

def ignore_patterns_list(patterns: List[str]) -> Any:
    """Helper - returns a callable for shutil.copytree ignore."""
    # This tool might be tricky to expose directly via JSON.
    # Usually used internally. We'll return a string representation.
    return f"Ignore patterns callable for: {patterns}"

def count_files_recursive(path: str) -> int:
    """Count total files in tree."""
    count = 0
    for root, dirs, files in os.walk(path):
        count += len(files)
    return count

def get_directory_size(path: str) -> int:
    """Calculate total size of directory in bytes."""
    total = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            total += os.path.getsize(os.path.join(root, f))
    return total

def list_directory_recursive(path: str) -> List[str]:
    """Get all file paths in a tree."""
    paths = []
    for root, dirs, files in os.walk(path):
        for f in files:
            paths.append(os.path.join(root, f))
    return paths

def clean_directory(path: str) -> str:
    """Remove all files inside dir but keep dir."""
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        if os.path.isfile(item_path):
            os.remove(item_path)
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)
    return f"Cleaned contents of {path}"
