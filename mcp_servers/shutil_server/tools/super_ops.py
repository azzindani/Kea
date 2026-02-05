import shutil
import os
import datetime
import hashlib
from pathlib import Path
from typing import List, Dict, Any
from mcp_servers.shutil_server.tools import archive_ops

def synchronize_directories(src: str, dst: str) -> Dict[str, Any]:
    """One-way sync Source -> Dest (overwrite changed). Does NOT delete files in dst not in src."""
    # This is a naive sync. For robust sync, rsync is better, but this is pure python.
    stats = {"copied": 0, "updated": 0, "errors": []}
    src_path = Path(src)
    dst_path = Path(dst)
    
    if not src_path.exists():
        return {"error": "Source does not exist"}
        
    for root, dirs, files in os.walk(src):
        rel_root = Path(root).relative_to(src_path)
        target_root = dst_path / rel_root
        target_root.mkdir(parents=True, exist_ok=True)
        
        for f in files:
            s_file = Path(root) / f
            d_file = target_root / f
            
            should_copy = False
            if not d_file.exists():
                should_copy = True
            else:
                # Check mtime or size
                if s_file.stat().st_mtime > d_file.stat().st_mtime or s_file.stat().st_size != d_file.stat().st_size:
                    should_copy = True
                    stats["updated"] += 1
            
            if should_copy:
                try:
                    shutil.copy2(s_file, d_file)
                    stats["copied"] += 1
                except Exception as e:
                    stats["errors"].append(f"{s_file}: {e}")
                    
    return stats

def backup_directory(path: str, backup_dir: str) -> str:
    """Archive directory with timestamped filename."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = Path(path).name
    archive_name = f"{base_name}_backup_{timestamp}"
    full_path = str(Path(backup_dir) / archive_name)
    
    return archive_ops.make_archive(full_path, "zip", path)

def safe_delete(files: List[str], trash_dir: str) -> List[str]:
    """Move files to a `Trash/` or `tmp/` folder instead of deleting."""
    Path(trash_dir).mkdir(parents=True, exist_ok=True)
    results = []
    for f in files:
        if os.path.exists(f):
            try:
                # Append timestamp to handle duplicates in trash
                ts = datetime.datetime.now().strftime("%f")
                dest_name = f"{Path(f).name}_{ts}"
                shutil.move(f, str(Path(trash_dir) / dest_name))
                results.append(f"Trashed: {f}")
            except Exception as e:
                results.append(f"Error {f}: {e}")
    return results

def organize_by_extension(directory: str) -> Dict[str, int]:
    """Move files into `Ext/` folders (e.g. .txt -> txt/)."""
    stats = {}
    p = Path(directory)
    for f in p.iterdir():
        if f.is_file() and not f.name.startswith("."):
            ext = f.suffix.lstrip(".").lower()
            if not ext: ext = "no_ext"
            
            target_dir = p / ext
            target_dir.mkdir(exist_ok=True)
            try:
                shutil.move(str(f), str(target_dir / f.name))
                stats[ext] = stats.get(ext, 0) + 1
            except:
                pass
    return stats

def organize_by_date(directory: str) -> Dict[str, int]:
    """Move files into `YYYY-MM/` folders based on modification time."""
    stats = {}
    p = Path(directory)
    for f in p.iterdir():
        if f.is_file() and not f.name.startswith("."):
            mtime = datetime.datetime.fromtimestamp(f.stat().st_mtime)
            folder_name = mtime.strftime("%Y-%m")
            
            target_dir = p / folder_name
            target_dir.mkdir(exist_ok=True)
            try:
                shutil.move(str(f), str(target_dir / f.name))
                stats[folder_name] = stats.get(folder_name, 0) + 1
            except:
                pass
    return stats

def deep_clean_temp(directory: str) -> List[str]:
    """Remove common temp files (.tmp, .log, __pycache__) recursively."""
    deleted = []
    patterns = ["*.tmp", "*.log", "*.bak", "*.swp"]
    dirs_to_remove = ["__pycache__", ".ipynb_checkpoints"]
    
    p = Path(directory)
    
    # Remove files
    for pat in patterns:
        for f in p.rglob(pat):
            try:
                f.unlink()
                deleted.append(str(f))
            except:
                pass
    
    # Remove dirs
    for root, dirs, files in os.walk(directory):
        for d in dirs:
            if d in dirs_to_remove:
                full_path = os.path.join(root, d)
                try:
                    shutil.rmtree(full_path)
                    deleted.append(full_path)
                except:
                    pass
    return deleted

def find_duplicates_and_act(directory: str, action: str = "report") -> Dict[str, Any]:
    """Find content duplicates (MD5 hash) and (report/delete)."""
    hashes = {}
    duplicates = {}
    
    p = Path(directory)
    for f in p.rglob("*"):
        if f.is_file():
            try:
                file_hash = hashlib.md5(f.read_bytes()).hexdigest()
                if file_hash in hashes:
                    original = hashes[file_hash]
                    duplicates.setdefault(original, []).append(str(f))
                    
                    if action == "delete":
                        f.unlink()
                else:
                    hashes[file_hash] = str(f)
            except:
                pass 
                
    return {
        "action_taken": action,
        "duplicate_sets_found": len(duplicates),
        "details": duplicates if action == "report" else "Duplicates deleted"
    }
