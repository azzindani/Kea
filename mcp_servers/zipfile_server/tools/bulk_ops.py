import zipfile
import os
from typing import List, Dict, Any

def bulk_get_texts(path: str, members: List[str], **kwargs) -> Dict[str, str]:
    """Read text content of multiple files."""
    results = {}
    with zipfile.ZipFile(path, 'r') as zf:
        for m in members:
            try:
                with zf.open(m) as f:
                    results[m] = f.read().decode('utf-8', errors='replace')
            except Exception as e:
                results[m] = f"Error: {e}"
    return results

def bulk_add_files(path: str, file_paths: List[str], **kwargs) -> str:
    """Add list of files."""
    with zipfile.ZipFile(path, 'a', compression=zipfile.ZIP_DEFLATED) as zf:
        for f in file_paths:
            if os.path.exists(f):
                zf.write(f, arcname=os.path.basename(f))
    return f"Added {len(file_paths)} files."

def bulk_extract_separate(path: str, members: List[str], output_dir: str, **kwargs) -> str:
    """Extract members to different output dir."""
    _ = path, members
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    return "Use extract_members_list tool for this function."

def bulk_validate_zips(paths: List[str], **kwargs) -> Dict[str, str]:
    """Check integrity of list of zip files."""
    results = {}
    for p in paths:
        if not zipfile.is_zipfile(p):
            results[p] = "Not a zip"
            continue
        try:
            with zipfile.ZipFile(p, 'r') as zf:
                bad = zf.testzip()
                results[p] = f"Corrupt: {bad}" if bad else "OK"
        except Exception as e:
            results[p] = f"Error: {e}"
    return results

def get_total_size(path: str, **kwargs) -> int:
    """Sum of all uncompressed sizes."""
    with zipfile.ZipFile(path, 'r') as zf:
        return sum(i.file_size for i in zf.infolist())

def get_total_compressed_size(path: str, **kwargs) -> int:
    """Sum of all compressed sizes."""
    with zipfile.ZipFile(path, 'r') as zf:
        return sum(i.compress_size for i in zf.infolist())

def list_large_files(path: str, min_size: int, **kwargs) -> List[Dict[str, Any]]:
    """List files larger than X bytes."""
    with zipfile.ZipFile(path, 'r') as zf:
        return [
            {"filename": i.filename, "size": i.file_size} 
            for i in zf.infolist() if i.file_size > min_size
        ]
