import hashlib
from typing import Dict, Any

def shake_128_string(text: str, length: int) -> str:
    """Variable length digest using SHAKE128."""
    try:
        if not hasattr(hashlib, 'shake_128'):
            return "Error: SHAKE128 not available"
        h = hashlib.shake_128(text.encode('utf-8'))
        return h.hexdigest(length)
    except Exception as e:
        return f"Error: {e}"

def shake_256_string(text: str, length: int) -> str:
    """Variable length digest using SHAKE256."""
    try:
        if not hasattr(hashlib, 'shake_256'):
            return "Error: SHAKE256 not available"
        h = hashlib.shake_256(text.encode('utf-8'))
        return h.hexdigest(length)
    except Exception as e:
        return f"Error: {e}"
