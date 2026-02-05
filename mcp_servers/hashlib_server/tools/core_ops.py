import hashlib
import structlog
from typing import Dict, Any, List, Set

logger = structlog.get_logger()

def algorithms_guaranteed() -> List[str]:
    """List algorithms guaranteed on all platforms."""
    return sorted(list(hashlib.algorithms_guaranteed))

def algorithms_available() -> List[str]:
    """List all algorithms available in OpenSSL."""
    return sorted(list(hashlib.algorithms_available))

def get_hash_info(algo_name: str) -> Dict[str, Any]:
    """Get block size/digest size for algorithm."""
    try:
        h = hashlib.new(algo_name)
        return {
            "name": h.name,
            "digest_size": h.digest_size,
            "block_size": getattr(h, "block_size", "unknown"),
            "guaranteed": algo_name in hashlib.algorithms_guaranteed
        }
    except ValueError:
        return {"error": f"Algorithm {algo_name} not found"}
    except Exception as e:
        return {"error": str(e)}

def check_algorithm(algo_name: str) -> bool:
    """Verify if algo is supported."""
    return algo_name in hashlib.algorithms_available
