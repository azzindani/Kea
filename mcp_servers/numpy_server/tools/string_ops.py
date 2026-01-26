from mcp_servers.numpy_server.tools.core_ops import to_serializable, NumericData
import numpy as np
from typing import Dict, Any, List, Optional, Union

# Helper for string arrays via core_ops logic isn't fully tuned for strings 
# since `parse_array` tries to be numeric. We'll make a local helper.
def _parse_str_array(data: Any) -> np.ndarray:
    try:
        if isinstance(data, str):
            # Try JSON first for list of strings
            import json
            try:
                parsed = json.loads(data)
                return np.array(parsed, dtype=str)
            except:
                # Comma separated
                if "," in data:
                    return np.array([x.strip() for x in data.split(",")], dtype=str)
                return np.array([data], dtype=str)
        return np.array(data, dtype=str)
    except Exception as e:
        raise ValueError(f"Could not parse string data: {e}")

async def char_add(x1: Union[List[str], str], x2: Union[List[str], str]) -> List[str]:
    """Return element-wise string concatenation."""
    return to_serializable(np.char.add(_parse_str_array(x1), _parse_str_array(x2)).tolist())

async def char_multiply(a: Union[List[str], str], i: int) -> List[str]:
    """Return multiple concatenation element-wise."""
    return to_serializable(np.char.multiply(_parse_str_array(a), i).tolist())

async def char_upper(a: Union[List[str], str]) -> List[str]:
    """Return an array with the elements converted to uppercase."""
    return to_serializable(np.char.upper(_parse_str_array(a)).tolist())

async def char_lower(a: Union[List[str], str]) -> List[str]:
    """Return an array with the elements converted to lowercase."""
    return to_serializable(np.char.lower(_parse_str_array(a)).tolist())

async def char_capitalize(a: Union[List[str], str]) -> List[str]:
    """Return a copy of the array with only the first character of each element capitalized."""
    return to_serializable(np.char.capitalize(_parse_str_array(a)).tolist())

async def char_title(a: Union[List[str], str]) -> List[str]:
    """Return element-wise title cased version of string or unicode."""
    return to_serializable(np.char.title(_parse_str_array(a)).tolist())

async def char_strip(a: Union[List[str], str], chars: Optional[str] = None) -> List[str]:
    """For each element in a, return a copy with the leading and trailing characters removed."""
    return to_serializable(np.char.strip(_parse_str_array(a), chars=chars).tolist())

async def char_replace(a: Union[List[str], str], old: str, new: str, count: Optional[int] = None) -> List[str]:
    """For each element in a, return a copy of the string with all occurrences of substring old replaced by new."""
    return to_serializable(np.char.replace(_parse_str_array(a), old, new, count=count).tolist())

async def char_compare_equal(x1: Union[List[str], str], x2: Union[List[str], str]) -> List[bool]:
    """Return (x1 == x2) element-wise."""
    return to_serializable(np.char.equal(_parse_str_array(x1), _parse_str_array(x2)).tolist())

async def char_count(a: Union[List[str], str], sub: str, start: int = 0, end: Optional[int] = None) -> List[int]:
    """Returns an array with the number of non-overlapping occurrences of substring sub in a[i]."""
    return to_serializable(np.char.count(_parse_str_array(a), sub, start, end).tolist())

async def char_find(a: Union[List[str], str], sub: str, start: int = 0, end: Optional[int] = None) -> List[int]:
    """For each element, return the lowest index in the string where substring sub is found."""
    return to_serializable(np.char.find(_parse_str_array(a), sub, start, end).tolist())
