import shutil
import os
from pathlib import Path
from typing import List, Dict, Any

def bulk_copy_files(files: List[str], destination_dir: str) -> List[str]:
    """Copy list of files to destination dir."""
    results = []
    Path(destination_dir).mkdir(parents=True, exist_ok=True)
    for f in files:
        if os.path.exists(f):
            try:
                res = shutil.copy(f, destination_dir)
                results.append(f"Success: {f} -> {res}")
            except Exception as e:
                results.append(f"Error {f}: {e}")
        else:
            results.append(f"Skip: {f} not found")
    return results

def bulk_move_files(files: List[str], destination_dir: str) -> List[str]:
    """Move list of files to destination dir."""
    results = []
    Path(destination_dir).mkdir(parents=True, exist_ok=True)
    for f in files:
        if os.path.exists(f):
            try:
                res = shutil.move(f, destination_dir)
                results.append(f"Success: {f} -> {res}")
            except Exception as e:
                results.append(f"Error {f}: {e}")
        else:
            results.append(f"Skip: {f} not found")
    return results

def bulk_delete_files(files: List[str]) -> List[str]:
    """Delete list of files."""
    results = []
    for f in files:
        if os.path.exists(f):
            try:
                os.remove(f)
                results.append(f"Deleted: {f}")
            except Exception as e:
                results.append(f"Error {f}: {e}")
        else:
            results.append(f"Skip: {f} not found")
    return results

def bulk_rename_files(files: List[str], prefix: str = "", suffix: str = "") -> List[str]:
    """Rename multiple files (e.g., prefix/suffix) in place."""
    results = []
    for f in files:
        if os.path.exists(f):
            p = Path(f)
            new_name = f"{prefix}{p.stem}{suffix}{p.suffix}"
            new_path = p.parent / new_name
            try:
                p.rename(new_path)
                results.append(f"Renamed: {p.name} -> {new_name}")
            except Exception as e:
                results.append(f"Error {f}: {e}")
    return results

def bulk_change_extension(files: List[str], new_extension: str) -> List[str]:
    """Change extension for list of files (e.g. .txt to .md)."""
    # extension should include dot, e.g. ".md"
    results = []
    for f in files:
        if os.path.exists(f):
            p = Path(f)
            new_path = p.with_suffix(new_extension)
            try:
                p.rename(new_path)
                results.append(f"Changed: {p.name} -> {new_path.name}")
            except Exception as e:
                results.append(f"Error {f}: {e}")
    return results

def copy_files_by_pattern(source_dir: str, pattern: str, destination_dir: str) -> List[str]:
    """Copy files matching glob pattern."""
    p = Path(source_dir)
    files = [str(f) for f in p.glob(pattern) if f.is_file()]
    return bulk_copy_files(files, destination_dir)

def move_files_by_pattern(source_dir: str, pattern: str, destination_dir: str) -> List[str]:
    """Move files matching glob pattern."""
    p = Path(source_dir)
    files = [str(f) for f in p.glob(pattern) if f.is_file()]
    return bulk_move_files(files, destination_dir)

def delete_files_by_pattern(source_dir: str, pattern: str) -> List[str]:
    """Delete files matching glob pattern."""
    p = Path(source_dir)
    files = [str(f) for f in p.glob(pattern) if f.is_file()]
    return bulk_delete_files(files)
