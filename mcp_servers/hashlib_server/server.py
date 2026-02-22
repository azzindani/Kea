
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "mcp",
#   "structlog",
# ]
# ///

from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.hashlib_server.tools import (
    core_ops, string_ops, shake_ops, file_ops, bulk_ops, security_ops, super_ops
)
import structlog
from typing import Dict, Any, List, Optional

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging(force_stderr=True)

mcp = FastMCP("hashlib_server")

# ==========================================
# 1. Core
# ==========================================
# ==========================================
# 1. Core
# ==========================================
@mcp.tool()
def algorithms_guaranteed() -> List[str]: 
    """LISTS guaranteed. [ACTION]
    
    [RAG Context]
    List algorithms guaranteed across all platforms.
    Returns list of strings.
    """
    return core_ops.algorithms_guaranteed()

@mcp.tool()
def algorithms_available() -> List[str]: 
    """LISTS available. [ACTION]
    
    [RAG Context]
    List all available algorithms on this system.
    Returns list of strings.
    """
    return core_ops.algorithms_available()

@mcp.tool()
def get_hash_info(algo_name: str) -> Dict[str, Any]: 
    """FETCHES hash info. [ACTION]
    
    [RAG Context]
    Get details (digest size, block size) for algorithm.
    Returns JSON dict.
    """
    return core_ops.get_hash_info(algo_name)

@mcp.tool()
def check_algorithm(algo_name: str) -> bool: 
    """CHECKS algorithm. [ACTION]
    
    [RAG Context]
    Verify if an algorithm is supported.
    Returns boolean.
    """
    return core_ops.check_algorithm(algo_name)

# ==========================================
# 2. String
# ==========================================
@mcp.tool()
def md5_string(text: str) -> str: 
    """HASHES MD5. [ACTION]
    
    [RAG Context]
    Calculate MD5 hash of string.
    Returns hex string.
    """
    return string_ops.md5_string(text)

@mcp.tool()
def sha1_string(text: str) -> str: 
    """HASHES SHA1. [ACTION]
    
    [RAG Context]
    Calculate SHA1 hash of string.
    Returns hex string.
    """
    return string_ops.sha1_string(text)

@mcp.tool()
def sha224_string(text: str) -> str: 
    """HASHES SHA224. [ACTION]
    
    [RAG Context]
    Calculate SHA224 hash of string.
    Returns hex string.
    """
    return string_ops.sha224_string(text)

@mcp.tool()
def sha256_string(text: str) -> str: 
    """HASHES SHA256. [ACTION]
    
    [RAG Context]
    Calculate SHA256 hash of string.
    Returns hex string.
    """
    return string_ops.sha256_string(text)

@mcp.tool()
def sha384_string(text: str) -> str: 
    """HASHES SHA384. [ACTION]
    
    [RAG Context]
    Calculate SHA384 hash of string.
    Returns hex string.
    """
    return string_ops.sha384_string(text)

@mcp.tool()
def sha512_string(text: str) -> str: 
    """HASHES SHA512. [ACTION]
    
    [RAG Context]
    Calculate SHA512 hash of string.
    Returns hex string.
    """
    return string_ops.sha512_string(text)

@mcp.tool()
def sha3_224_string(text: str) -> str: 
    """HASHES SHA3-224. [ACTION]
    
    [RAG Context]
    Calculate SHA3-224 hash of string.
    Returns hex string.
    """
    return string_ops.sha3_224_string(text)

@mcp.tool()
def sha3_256_string(text: str) -> str: 
    """HASHES SHA3-256. [ACTION]
    
    [RAG Context]
    Calculate SHA3-256 hash of string.
    Returns hex string.
    """
    return string_ops.sha3_256_string(text)

@mcp.tool()
def sha3_384_string(text: str) -> str: 
    """HASHES SHA3-384. [ACTION]
    
    [RAG Context]
    Calculate SHA3-384 hash of string.
    Returns hex string.
    """
    return string_ops.sha3_384_string(text)

@mcp.tool()
def sha3_512_string(text: str) -> str: 
    """HASHES SHA3-512. [ACTION]
    
    [RAG Context]
    Calculate SHA3-512 hash of string.
    Returns hex string.
    """
    return string_ops.sha3_512_string(text)

@mcp.tool()
def blake2b_string(text: str, digest_size: int = 64) -> str: 
    """HASHES BLAKE2b. [ACTION]
    
    [RAG Context]
    Calculate BLAKE2b hash of string.
    Returns hex string.
    """
    return string_ops.blake2b_string(text, digest_size)

@mcp.tool()
def blake2s_string(text: str, digest_size: int = 32) -> str: 
    """HASHES BLAKE2s. [ACTION]
    
    [RAG Context]
    Calculate BLAKE2s hash of string.
    Returns hex string.
    """
    return string_ops.blake2s_string(text, digest_size)

@mcp.tool()
def hash_string_generic(text: str, algo_name: str) -> str: 
    """HASHES generic. [ACTION]
    
    [RAG Context]
    Calculate any supported hash of string.
    Returns hex string.
    """
    return string_ops.hash_string_generic(text, algo_name)

# ==========================================
# 3. Shake
# ==========================================
@mcp.tool()
def shake_128_string(text: str, length: int) -> str: 
    """HASHES SHAKE-128. [ACTION]
    
    [RAG Context]
    Calculate variable-length SHAKE-128 hash.
    Returns hex string.
    """
    return shake_ops.shake_128_string(text, length)

@mcp.tool()
def shake_256_string(text: str, length: int) -> str: 
    """HASHES SHAKE-256. [ACTION]
    
    [RAG Context]
    Calculate variable-length SHAKE-256 hash.
    Returns hex string.
    """
    return shake_ops.shake_256_string(text, length)

# ==========================================
# 4. File
# ==========================================
@mcp.tool()
def md5_file(file_path: str) -> str: 
    """HASHES file MD5. [ACTION]
    
    [RAG Context]
    Calculate MD5 hash of file.
    Returns hex string.
    """
    return file_ops.md5_file(file_path)

@mcp.tool()
def sha1_file(file_path: str) -> str: 
    """HASHES file SHA1. [ACTION]
    
    [RAG Context]
    Calculate SHA1 hash of file.
    Returns hex string.
    """
    return file_ops.sha1_file(file_path)

@mcp.tool()
def sha256_file(file_path: str) -> str: 
    """HASHES file SHA256. [ACTION]
    
    [RAG Context]
    Calculate SHA256 hash of file.
    Returns hex string.
    """
    return file_ops.sha256_file(file_path)

@mcp.tool()
def sha512_file(file_path: str) -> str: 
    """HASHES file SHA512. [ACTION]
    
    [RAG Context]
    Calculate SHA512 hash of file.
    Returns hex string.
    """
    return file_ops.sha512_file(file_path)

@mcp.tool()
def blake2b_file(file_path: str) -> str: 
    """HASHES file BLAKE2b. [ACTION]
    
    [RAG Context]
    Calculate BLAKE2b hash of file.
    Returns hex string.
    """
    return file_ops.blake2b_file(file_path)

@mcp.tool()
def hash_file_generic(file_path: str, algo_name: str) -> str: 
    """HASHES file generic. [ACTION]
    
    [RAG Context]
    Calculate any supported hash of file.
    Returns hex string.
    """
    return file_ops.hash_file_generic(file_path, algo_name)

@mcp.tool()
def hash_file_partial(file_path: str, algo_name: str, chunk_size: int = 1024) -> str: 
    """HASHES file partial. [ACTION]
    
    [RAG Context]
    Calculate hash of first N bytes of file.
    Returns hex string.
    """
    return file_ops.hash_file_partial(file_path, algo_name, chunk_size)

# ==========================================
# 5. Bulk
# ==========================================
# ==========================================
# 5. Bulk
# ==========================================
@mcp.tool()
def bulk_hash_strings(texts: List[str], algo: str = "sha256") -> List[str]: 
    """BULK: Hash Strings. [ACTION]
    
    [RAG Context]
    Hash multiple strings.
    Returns list of hex strings.
    """
    return bulk_ops.bulk_hash_strings(texts, algo)

@mcp.tool()
def bulk_hash_files(file_paths: List[str], algo: str = "sha256") -> Dict[str, str]: 
    """BULK: Hash Files. [ACTION]
    
    [RAG Context]
    Hash multiple files.
    Returns dict of path->hex.
    """
    return bulk_ops.bulk_hash_files(file_paths, algo)

@mcp.tool()
def hash_directory(directory: str, algo: str = "sha256", recursive: bool = True, pattern: str = "*") -> Dict[str, str]: 
    """HASHES directory. [ACTION]
    
    [RAG Context]
    Recursively hash all files in directory.
    Returns dict of path->hex.
    """
    return bulk_ops.hash_directory(directory, algo, recursive, pattern)

@mcp.tool()
def hash_directory_manifest(directory: str, algo: str = "sha256") -> str: 
    """GENERATES manifest. [ACTION]
    
    [RAG Context]
    Create JSON manifest of directory hashes.
    Returns JSON string.
    """
    return bulk_ops.hash_directory_manifest(directory, algo)

# ==========================================
# 6. Security
# ==========================================
@mcp.tool()
def hmac_string(key: str, message: str, algo: str = "sha256") -> str: 
    """CALCULATES HMAC. [ACTION]
    
    [RAG Context]
    Calculate HMAC for string.
    Returns hex string.
    """
    return security_ops.hmac_string(key, message, algo)

@mcp.tool()
def hmac_file(key: str, file_path: str, algo: str = "sha256") -> str: 
    """CALCULATES HMAC file. [ACTION]
    
    [RAG Context]
    Calculate HMAC for file content.
    Returns hex string.
    """
    return security_ops.hmac_file(key, file_path, algo)

@mcp.tool()
def pbkdf2_hmac(password: str, salt: str, iterations: int = 100000, dklen: int = 32, algo: str = "sha256") -> str: 
    """DERIVES key (PBKDF2). [ACTION]
    
    [RAG Context]
    Derive key using PBKDF2.
    Returns hex string.
    """
    return security_ops.pbkdf2_hmac(password, salt, iterations, dklen, algo)

@mcp.tool()
def scrypt_kdf(password: str, salt: str, n: int = 16384, r: int = 8, p: int = 1, dklen: int = 32) -> str: 
    """DERIVES key (scrypt). [ACTION]
    
    [RAG Context]
    Derive key using scrypt.
    Returns hex string.
    """
    return security_ops.scrypt_kdf(password, salt, n, r, p, dklen)

@mcp.tool()
def verify_hmac(key: str, message: str, signature: str, algo: str = "sha256") -> bool: 
    """VERIFIES HMAC. [ACTION]
    
    [RAG Context]
    Verify HMAC signature (timing-safe).
    Returns boolean.
    """
    return security_ops.verify_hmac(key, message, signature, algo)

# ==========================================
# 7. Super
# ==========================================
@mcp.tool()
def verify_file_checksum(file_path: str, expected_hash: str, algo: str = "sha256") -> bool: 
    """VERIFIES checksum. [ACTION]
    
    [RAG Context]
    Verify file matches expected hash.
    Returns boolean.
    """
    return super_ops.verify_file_checksum(file_path, expected_hash, algo)

@mcp.tool()
def find_duplicates(directory: str, algo: str = "sha256") -> Dict[str, List[str]]: 
    """FINDS duplicates. [ACTION]
    
    [RAG Context]
    Find duplicate files by hash.
    Returns dict of hash->[paths].
    """
    return super_ops.find_duplicates(directory, algo)

@mcp.tool()
def generate_dir_fingerprint(directory: str, algo: str = "sha256") -> str: 
    """FINGERPRINTS dir. [ACTION]
    
    [RAG Context]
    Calculate single hash for entire directory state.
    Returns hex string.
    """
    return super_ops.generate_dir_fingerprint(directory, algo)

@mcp.tool()
def compare_directories(dir_a: str, dir_b: str, algo: str = "sha256") -> Dict[str, List[str]]: 
    """COMPARES dirs. [ACTION]
    
    [RAG Context]
    Compare two directories by hash.
    Returns dict of differences.
    """
    return super_ops.compare_directories(dir_a, dir_b, algo)

@mcp.tool()
def verify_manifest(manifest_json: str, base_dir: str) -> Dict[str, str]: 
    """VERIFIES manifest. [ACTION]
    
    [RAG Context]
    Verify directory against manifest.
    Returns dict of mismatches.
    """
    return super_ops.verify_manifest(manifest_json, base_dir)

@mcp.tool()
def update_rolling_hash(current_hash: str, new_chunk: str, algo: str = "sha256") -> str: 
    """UPDATES rolling hash. [ACTION]
    
    [RAG Context]
    Update hash with new data chunk.
    Returns hex string.
    """
    return super_ops.update_rolling_hash(current_hash, new_chunk, algo)

@mcp.tool()
def hash_url_content(url: str, algo: str = "sha256") -> str: 
    """HASHES URL. [ACTION]
    
    [RAG Context]
    Download and hash URL content.
    Returns hex string.
    """
    return super_ops.hash_url_content(url, algo)

@mcp.tool()
def detect_hash_type(hash_str: str) -> List[str]: 
    """DETECTS hash type. [ACTION]
    
    [RAG Context]
    Identify possible algorithms for a hash string.
    Returns list of algo names.
    """
    return super_ops.detect_hash_type(hash_str)

@mcp.tool()
def generate_random_token(bytes_len: int = 32) -> str: 
    """GENERATES token. [ACTION]
    
    [RAG Context]
    Generate cryptographically strong random token.
    Returns hex string.
    """
    return super_ops.generate_random_token(bytes_len)

@mcp.tool()
def benchmark_algorithms(payload_size_mb: int = 10) -> Dict[str, float]: 
    """BENCHMARKS algos. [ACTION]
    
    [RAG Context]
    Measure speed of available algorithms.
    Returns dict of algo->speed.
    """
    return super_ops.benchmark_algorithms(payload_size_mb)

@mcp.tool()
def monitor_file_changes(file_path: str, checks: int = 3, interval: float = 1.0) -> str: 
    """MONITORS file. [ACTION]
    
    [RAG Context]
    Watch file for hash changes.
    Returns report string.
    """
    return super_ops.monitor_file_changes(file_path, checks, interval)

@mcp.tool()
def hash_csv_rows(input_csv: str, output_csv: str, algo: str = "sha256") -> str: 
    """HASHES CSV rows. [ACTION]
    
    [RAG Context]
    Add hash column to CSV file.
    Returns output path.
    """
    return super_ops.hash_csv_rows(input_csv, output_csv, algo)

@mcp.tool()
def verify_password_pbkdf2(password: str, stored_hash: str, salt: str, iterations: int = 100000) -> bool: 
    """VERIFIES password. [ACTION]
    
    [RAG Context]
    Verify password against PBKDF2 hash.
    Returns boolean.
    """
    return super_ops.verify_password_pbkdf2(password, stored_hash, salt, iterations)

@mcp.tool()
def create_merkle_root(items: List[str], algo: str = "sha256") -> str: 
    """CREATES Merkle root. [ACTION]
    
    [RAG Context]
    Calculate Merkle Root for list of items.
    Returns hex string.
    """
    return super_ops.create_merkle_root(items, algo)

@mcp.tool()
def compare_text_similarity(text1: str, text2: str) -> float: 
    """COMPARES similarity. [ACTION]
    
    [RAG Context]
    Compare text similarity using MinHash.
    Returns float (0-1).
    """
    return super_ops.compare_text_similarity(text1, text2)

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class HashlibServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []

