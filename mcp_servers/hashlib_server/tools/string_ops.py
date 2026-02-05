import hashlib
from typing import Dict, Any, Optional

def _hash_string(text: str, algo: str) -> str:
    h = hashlib.new(algo)
    h.update(text.encode('utf-8'))
    return h.hexdigest()

def md5_string(text: str) -> str: return _hash_string(text, 'md5')
def sha1_string(text: str) -> str: return _hash_string(text, 'sha1')
def sha224_string(text: str) -> str: return _hash_string(text, 'sha224')
def sha256_string(text: str) -> str: return _hash_string(text, 'sha256')
def sha384_string(text: str) -> str: return _hash_string(text, 'sha384')
def sha512_string(text: str) -> str: return _hash_string(text, 'sha512')
def sha3_224_string(text: str) -> str: return _hash_string(text, 'sha3_224')
def sha3_256_string(text: str) -> str: return _hash_string(text, 'sha3_256')
def sha3_384_string(text: str) -> str: return _hash_string(text, 'sha3_384')
def sha3_512_string(text: str) -> str: return _hash_string(text, 'sha3_512')

def blake2b_string(text: str, digest_size: int = 64) -> str:
    """Hash string with BLAKE2b (64-bit). digest_size between 1 and 64."""
    try:
        h = hashlib.blake2b(text.encode('utf-8'), digest_size=digest_size)
        return h.hexdigest()
    except Exception as e:
        return f"Error: {e}"

def blake2s_string(text: str, digest_size: int = 32) -> str:
    """Hash string with BLAKE2s (32-bit). digest_size between 1 and 32."""
    try:
        h = hashlib.blake2s(text.encode('utf-8'), digest_size=digest_size)
        return h.hexdigest()
    except Exception as e:
        return f"Error: {e}"

def hash_string_generic(text: str, algo_name: str) -> str:
    """Hash string with arbitrary algo name."""
    try:
        return _hash_string(text, algo_name)
    except Exception as e:
        return f"Error: {e}"
