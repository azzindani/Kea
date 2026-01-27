import hashlib
import os
import glob
from typing import List, Dict, Any
from mcp_servers.hashlib_server.tools import file_ops, string_ops

def bulk_hash_strings(texts: List[str], algo: str = "sha256") -> List[str]:
    """Hash list of strings."""
    results = []
    for t in texts:
        try:
            results.append(string_ops.hash_string_generic(t, algo))
        except:
            results.append("Error")
    return results

def bulk_hash_files(file_paths: List[str], algo: str = "sha256") -> Dict[str, str]:
    """Hash list of file paths. Returns dict {path: hash}."""
    results = {}
    for p in file_paths:
        results[p] = file_ops.hash_file_generic(p, algo)
    return results

def hash_directory(directory: str, algo: str = "sha256", recursive: bool = True, pattern: str = "*") -> Dict[str, str]:
    """Recursive hash of all files in dir. Returns {relative_path: hash}."""
    results = {}
    if not os.path.isdir(directory):
        return {"error": "Not a directory"}
    
    # Use glob for pattern matching
    search_path = os.path.join(directory, "**", pattern) if recursive else os.path.join(directory, pattern)
    
    # glob.glob with recursive=True requires **
    files = glob.glob(search_path, recursive=recursive)
    
    for f in files:
        if os.path.isfile(f):
            # relative path key
            rel_path = os.path.relpath(f, directory)
            results[rel_path] = file_ops.hash_file_generic(f, algo)
            
    return results

def hash_directory_manifest(directory: str, algo: str = "sha256") -> str:
    """Create JSON manifest of dir."""
    import json
    hashes = hash_directory(directory, algo)
    return json.dumps(hashes, indent=2)
