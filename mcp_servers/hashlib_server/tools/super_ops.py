import hashlib
import os
import json
from typing import List, Dict, Any, Tuple
from mcp_servers.hashlib_server.tools import file_ops, bulk_ops, security_ops, string_ops

def verify_file_checksum(file_path: str, expected_hash: str, algo: str = "sha256") -> bool:
    """Compare file hash against expected hash."""
    actual = file_ops.hash_file_generic(file_path, algo)
    return actual.lower() == expected_hash.lower()

def find_duplicates(directory: str, algo: str = "sha256") -> Dict[str, List[str]]:
    """Scan directory, find duplicate files by hash. Returns {hash: [files]}."""
    prop_hashes = bulk_ops.hash_directory(directory, algo, recursive=True)
    if "error" in prop_hashes: return {}
    
    # Invert dictionary
    duplicates = {}
    for path, h in prop_hashes.items():
        if h not in duplicates:
            duplicates[h] = []
        duplicates[h].append(path)
    
    # Filter only those with count > 1
    return {h: paths for h, paths in duplicates.items() if len(paths) > 1}

def generate_dir_fingerprint(directory: str, algo: str = "sha256") -> str:
    """Single hash representing entire directory state (Merkle-ish)."""
    prop_hashes = bulk_ops.hash_directory(directory, algo, recursive=True)
    if "error" in prop_hashes: return "Error"
    
    # Sort keys to ensure deterministic order
    sorted_paths = sorted(prop_hashes.keys())
    
    # Hash the ordered string of (path + hash)
    meta_content = ""
    for p in sorted_paths:
        meta_content += f"{p}:{prop_hashes[p]}|"
        
    return string_ops.hash_string_generic(meta_content, algo)

def compare_directories(dir_a: str, dir_b: str, algo: str = "sha256") -> Dict[str, List[str]]:
    """Diff two directories based on content hashes."""
    hashes_a = bulk_ops.hash_directory(dir_a, algo)
    hashes_b = bulk_ops.hash_directory(dir_b, algo)
    
    only_in_a = []
    only_in_b = []
    modified = []
    
    all_files = set(hashes_a.keys()) | set(hashes_b.keys())
    
    for f in all_files:
        if f not in hashes_b:
            only_in_a.append(f)
        elif f not in hashes_a:
            only_in_b.append(f)
        elif hashes_a[f] != hashes_b[f]:
            modified.append(f)
            
    return {
        "only_in_a": only_in_a,
        "only_in_b": only_in_b,
        "modified": modified
    }

def verify_manifest(manifest_json: str, base_dir: str) -> Dict[str, str]:
    """Check files against a JSON manifest. Returns {file: status}."""
    try:
        expected = json.loads(manifest_json)
        results = {}
        for rel_path, expected_hash in expected.items():
            full_path = os.path.join(base_dir, rel_path)
            if not os.path.exists(full_path):
                results[rel_path] = "MISSING"
                continue
            
            # Infer algo from length? Assume sha256 default or check len
            # This is simple check
            actual = file_ops.hash_file_generic(full_path, "sha256") 
            if actual == expected_hash:
                results[rel_path] = "OK"
            else:
                results[rel_path] = "MISMATCH"
        return results
    except Exception as e:
        return {"error": str(e)}

def update_rolling_hash(current_hash: str, new_chunk: str, algo: str = "sha256") -> str:
    """Update hash with new chunk (stateful simulation - impractical for std hash).
    Real rolling hash (Adler32/Rabin) is different.
    This just hashes (current + new), chaining them.
    """
    combined = current_hash + new_chunk
    return string_ops.hash_string_generic(combined, algo)

def hash_url_content(url: str, algo: str = "sha256") -> str:
    """Download and hash URL (simple get)."""
    import urllib.request
    try:
        h = hashlib.new(algo)
        with urllib.request.urlopen(url) as response:
            while True:
                chunk = response.read(4096)
                if not chunk: break
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return f"Error: {e}"

def detect_hash_type(hash_str: str) -> List[str]:
    """Guess algo based on hex string length."""
    length = len(hash_str)
    # bytes = length / 2
    # bits = bytes * 8
    guesses = []
    if length == 32: guesses.append("md5")
    if length == 40: guesses.append("sha1") # or ripemd160
    if length == 56: guesses = ["sha224", "sha3_224"]
    if length == 64: guesses = ["sha256", "sha3_256", "blake2s"]
    if length == 96: guesses = ["sha384", "sha3_384"]
    if length == 128: guesses = ["sha512", "sha3_512", "blake2b"]
    
    return guesses if guesses else ["unknown"]

def generate_random_token(bytes_len: int = 32) -> str:
    """Use secrets (os.urandom) to make token."""
    import secrets
    return secrets.token_hex(bytes_len) # token_hex args is bytes, returns 2x chars

def benchmark_algorithms(payload_size_mb: int = 10) -> Dict[str, float]:
    """Speed test algos on current system."""
    import time
    data = b'a' * (1024 * 1024 * payload_size_mb)
    results = {}
    algos = ["md5", "sha1", "sha256", "sha512", "blake2b"]
    
    for a in algos:
        start = time.time()
        h = hashlib.new(a)
        h.update(data)
        d = h.digest()
        end = time.time()
        results[a] = round(end - start, 4)
    return results

def monitor_file_changes(file_path: str, checks: int = 3, interval: float = 1.0) -> str:
    """Check file hash periodically (simulation)."""
    import time
    if not os.path.exists(file_path): return "File not found"
    
    initial = file_ops.sha256_file(file_path)
    for i in range(checks):
        time.sleep(interval)
        current = file_ops.sha256_file(file_path)
        if current != initial:
            return f"Change detected at check {i+1}! Old: {initial[:8]}... New: {current[:8]}..."
    return "No changes detected."

def hash_csv_rows(input_csv: str, output_csv: str, algo: str = "sha256") -> str:
    """Add hash column to CSV."""
    import csv
    try:
        with open(input_csv, 'r', newline='', encoding='utf-8') as fin, \
             open(output_csv, 'w', newline='', encoding='utf-8') as fout:
            reader = csv.reader(fin)
            writer = csv.writer(fout)
            
            header = next(reader)
            writer.writerow(header + ["row_hash"])
            
            for row in reader:
                # Join cols to hash
                content = "".join(row)
                h = string_ops.hash_string_generic(content, algo)
                writer.writerow(row + [h])
        return f"Hashed rows to {output_csv}"
    except Exception as e:
        return f"Error: {e}"

def verify_password_pbkdf2(password: str, stored_hash: str, salt: str, iterations: int = 100000) -> bool:
    """Verify password storage."""
    new_hash = security_ops.pbkdf2_hmac(password, salt, iterations)
    return new_hash == stored_hash

def create_merkle_root(items: List[str], algo: str = "sha256") -> str:
    """Build Merkle root from list of items."""
    # 1. Hash all items
    hashes = [string_ops.hash_string_generic(i, algo) for i in items]
    
    # 2. Iteratively hash pairs
    while len(hashes) > 1:
        if len(hashes) % 2 != 0:
            hashes.append(hashes[-1]) # duplicate last
        
        new_level = []
        for i in range(0, len(hashes), 2):
            combined = hashes[i] + hashes[i+1]
            new_level.append(string_ops.hash_string_generic(combined, algo))
        hashes = new_level
        
    return hashes[0] if hashes else ""

def compare_text_similarity(text1: str, text2: str) -> float:
    """Fuzzy hash PLACEHOLDER (Jaccard on trigrams or similar)."""
    # Simple set overlap of words for now since SimHash needs dependency
    s1 = set(text1.split())
    s2 = set(text2.split())
    if not s1 or not s2: return 0.0
    return len(s1 & s2) / len(s1 | s2)
