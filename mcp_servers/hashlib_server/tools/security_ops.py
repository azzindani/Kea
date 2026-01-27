import hashlib
import hmac
import os
import secrets
from typing import Dict, Any

def hmac_string(key: str, message: str, algo: str = "sha256") -> str:
    """Create HMAC for string."""
    try:
        h = hmac.new(key.encode('utf-8'), message.encode('utf-8'), algo)
        return h.hexdigest()
    except Exception as e:
        return f"Error: {e}"

def hmac_file(key: str, file_path: str, algo: str = "sha256") -> str:
    """Create HMAC for file."""
    try:
        if not os.path.exists(file_path): return "Error: File not found"
        # Streaming HMAC
        h = hmac.new(key.encode('utf-8'), digestmod=algo)
        with open(file_path, 'rb') as f:
             for chunk in iter(lambda: f.read(4096 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return f"Error: {e}"

def pbkdf2_hmac(password: str, salt: str, iterations: int = 100000, dklen: int = 32, algo: str = "sha256") -> str:
    """Key derivation using PBKDF2."""
    try:
        # returns bytes, convert to hex
        dk = hashlib.pbkdf2_hmac(algo, password.encode('utf-8'), salt.encode('utf-8'), iterations, dklen)
        return dk.hex()
    except Exception as e:
        return f"Error: {e}"

def scrypt_kdf(password: str, salt: str, n: int = 16384, r: int = 8, p: int = 1, dklen: int = 32) -> str:
    """Key derivation using Scrypt (requires OpenSSL 1.1+)."""
    try:
        if not hasattr(hashlib, 'scrypt'):
            return "Error: Scrypt not available (needs Python 3.6+ and OpenSSL 1.1+)"
        dk = hashlib.scrypt(password.encode('utf-8'), salt=salt.encode('utf-8'), n=n, r=r, p=p, dklen=dklen)
        return dk.hex()
    except Exception as e:
        return f"Error: {e}"

def verify_hmac(key: str, message: str, signature: str, algo: str = "sha256") -> bool:
    """Verify digest matches message/key (constant time compare)."""
    try:
        expected = hmac.new(key.encode('utf-8'), message.encode('utf-8'), algo).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception:
        return False
