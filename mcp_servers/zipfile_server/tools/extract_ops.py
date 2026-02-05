import zipfile
import os
import re
from pathlib import Path
from typing import List, Optional

def _is_safe_path(base_dir: str, target_path: str) -> bool:
    """Prevent Zip Slip."""
    base = Path(base_dir).resolve()
    target = (base / target_path).resolve()
    return base in target.parents or base == target

def extract_all(path: str, extract_path: str, pwd: Optional[str] = None) -> str:
    """Extract entire archive to path (Safely)."""
    if not os.path.exists(extract_path):
        os.makedirs(extract_path)
    
    with zipfile.ZipFile(path, 'r') as zf:
        # Validation
        for member in zf.namelist():
            if not _is_safe_path(extract_path, member):
                return f"Error: Malicious path detected in zip: {member}"
        
        zf.extractall(extract_path, pwd=pwd.encode() if pwd else None)
        return f"Extracted to {extract_path}"

def extract_member(path: str, member: str, extract_path: str, pwd: Optional[str] = None) -> str:
    """Extract single file."""
    if not _is_safe_path(extract_path, member):
        return "Error: Unsafe path."
        
    with zipfile.ZipFile(path, 'r') as zf:
        zf.extract(member, extract_path, pwd=pwd.encode() if pwd else None)
        return f"Extracted {member}"

def extract_members_list(path: str, members: List[str], extract_path: str) -> str:
    """Extract specific list of files."""
    for m in members:
        if not _is_safe_path(extract_path, m): return f"Error: Unsafe path {m}"

    with zipfile.ZipFile(path, 'r') as zf:
        zf.extractall(extract_path, members=members)
        return f"Extracted {len(members)} files."

def extract_with_password(path: str, member: str, extract_path: str, pwd: str) -> str:
    """Extract using password."""
    return extract_member(path, member, extract_path, pwd)

def extract_by_pattern(path: str, pattern: str, extract_path: str) -> str:
    """Extract files matching regex."""
    regex = re.compile(pattern)
    with zipfile.ZipFile(path, 'r') as zf:
        members = [m for m in zf.namelist() if regex.search(m)]
        for m in members:
            if not _is_safe_path(extract_path, m): return "Unsafe path detected."
        
        zf.extractall(extract_path, members=members)
        return f"Extracted {len(members)} matching files."

def extract_by_extension(path: str, extension: str, extract_path: str) -> str:
    """Extract all .txt files etc."""
    # ext should include dot, e.g. ".txt"
    with zipfile.ZipFile(path, 'r') as zf:
        members = [m for m in zf.namelist() if m.endswith(extension)]
        zf.extractall(extract_path, members=members)
        return f"Extracted {len(members)} {extension} files."

def safe_extract(path: str, extract_path: str) -> str:
    """Extract preventing Zip Slip (path traversal check). Alias for extract_all with checks included."""
    return extract_all(path, extract_path)
