import hashlib
import os

def _hash_file(file_path: str, algo: str) -> str:
    try:
        h = hashlib.new(algo)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096 * 1024), b""): # 4MB chunks
                h.update(chunk)
        return h.hexdigest()
    except FileNotFoundError:
        return "Error: File not found"
    except Exception as e:
        return f"Error: {e}"

def md5_file(file_path: str) -> str: return _hash_file(file_path, 'md5')
def sha1_file(file_path: str) -> str: return _hash_file(file_path, 'sha1')
def sha256_file(file_path: str) -> str: return _hash_file(file_path, 'sha256')
def sha512_file(file_path: str) -> str: return _hash_file(file_path, 'sha512')

def blake2b_file(file_path: str) -> str:
    try:
        h = hashlib.blake2b()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return f"Error: {e}"

def hash_file_generic(file_path: str, algo_name: str) -> str:
    return _hash_file(file_path, algo_name)

def hash_file_partial(file_path: str, algo_name: str, chunk_size: int = 1024) -> str:
    """Hash first N and last N bytes (fingerprinting)."""
    try:
        h = hashlib.new(algo_name)
        size = os.path.getsize(file_path)
        with open(file_path, 'rb') as f:
            # First chunk
            h.update(f.read(chunk_size))
            # Last chunk if exists
            if size > chunk_size:
                f.seek(max(chunk_size, size - chunk_size))
                h.update(f.read())
        return h.hexdigest()
    except Exception as e:
        return f"Error: {e}"
