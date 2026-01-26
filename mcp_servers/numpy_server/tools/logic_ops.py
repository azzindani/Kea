from mcp_servers.numpy_server.tools.core_ops import parse_array, to_serializable, NumericData
import numpy as np
from typing import Dict, Any, List, Optional, Union

# ==========================================
# Comparisons
# ==========================================
async def greater(x1: NumericData, x2: NumericData) -> List[Any]:
    return to_serializable(np.greater(parse_array(x1), parse_array(x2)).tolist())

async def less(x1: NumericData, x2: NumericData) -> List[Any]:
    return to_serializable(np.less(parse_array(x1), parse_array(x2)).tolist())

async def equal(x1: NumericData, x2: NumericData) -> List[Any]:
    return to_serializable(np.equal(parse_array(x1), parse_array(x2)).tolist())

async def not_equal(x1: NumericData, x2: NumericData) -> List[Any]:
    return to_serializable(np.not_equal(parse_array(x1), parse_array(x2)).tolist())

# ==========================================
# Logical
# ==========================================
async def logical_and(x1: NumericData, x2: NumericData) -> List[Any]:
    return to_serializable(np.logical_and(parse_array(x1), parse_array(x2)).tolist())

async def logical_or(x1: NumericData, x2: NumericData) -> List[Any]:
    return to_serializable(np.logical_or(parse_array(x1), parse_array(x2)).tolist())

async def logical_not(x: NumericData) -> List[Any]:
    return to_serializable(np.logical_not(parse_array(x)).tolist())

async def all_true(a: NumericData, axis: Optional[int] = None) -> Union[bool, List[bool]]:
    res = np.all(parse_array(a), axis=axis)
    return to_serializable(res.tolist())

async def any_true(a: NumericData, axis: Optional[int] = None) -> Union[bool, List[bool]]:
    res = np.any(parse_array(a), axis=axis)
    return to_serializable(res.tolist())

# ==========================================
# Searching / Sorting
# ==========================================
async def where(condition: NumericData, x: Optional[NumericData] = None, y: Optional[NumericData] = None) -> List[Any]:
    cond = parse_array(condition) # Might be bool array or int
    if x is not None and y is not None:
        res = np.where(cond, parse_array(x), parse_array(y))
        return to_serializable(res.tolist())
    else:
        # Returns indices
        res = np.where(cond)
        return [to_serializable(r.tolist()) for r in res]

async def argmax(a: NumericData, axis: Optional[int] = None) -> Union[int, List[int]]:
    res = np.argmax(parse_array(a), axis=axis)
    return to_serializable(res.tolist())

async def argmin(a: NumericData, axis: Optional[int] = None) -> Union[int, List[int]]:
    res = np.argmin(parse_array(a), axis=axis)
    return to_serializable(res.tolist())

async def argsort(a: NumericData, axis: int = -1) -> List[Any]:
    res = np.argsort(parse_array(a), axis=axis)
    return to_serializable(res.tolist())

async def sort(a: NumericData, axis: int = -1) -> List[Any]:
    res = np.sort(parse_array(a), axis=axis)
    return to_serializable(res.tolist())

async def searchsorted(a: NumericData, v: NumericData, side: str = 'left') -> List[Any]:
    res = np.searchsorted(parse_array(a), parse_array(v), side=side)
    return to_serializable(res.tolist())
