from mcp_servers.numpy_server.tools.core_ops import parse_array, to_serializable, NumericData
import numpy as np
from typing import Dict, Any, List, Optional, Union

# ==========================================
# Arithmetic
# ==========================================
async def add(x1: NumericData, x2: NumericData) -> List[Any]:
    return to_serializable((parse_array(x1) + parse_array(x2)).tolist())

async def subtract(x1: NumericData, x2: NumericData) -> List[Any]:
    return to_serializable((parse_array(x1) - parse_array(x2)).tolist())

async def multiply(x1: NumericData, x2: NumericData) -> List[Any]:
    return to_serializable((parse_array(x1) * parse_array(x2)).tolist())

async def divide(x1: NumericData, x2: NumericData) -> List[Any]:
    return to_serializable((parse_array(x1) / parse_array(x2)).tolist())

async def power(x1: NumericData, x2: NumericData) -> List[Any]:
    return to_serializable(np.power(parse_array(x1), parse_array(x2)).tolist())

async def mod(x1: NumericData, x2: NumericData) -> List[Any]:
    return to_serializable(np.mod(parse_array(x1), parse_array(x2)).tolist())

# ==========================================
# Functions
# ==========================================
async def abs_val(x: NumericData) -> List[Any]:
    return to_serializable(np.abs(parse_array(x)).tolist())

async def sign(x: NumericData) -> List[Any]:
    return to_serializable(np.sign(parse_array(x)).tolist())

async def exp(x: NumericData) -> List[Any]:
    return to_serializable(np.exp(parse_array(x)).tolist())

async def log(x: NumericData) -> List[Any]:
    return to_serializable(np.log(parse_array(x)).tolist())

async def log10(x: NumericData) -> List[Any]:
    return to_serializable(np.log10(parse_array(x)).tolist())

async def sqrt(x: NumericData) -> List[Any]:
    return to_serializable(np.sqrt(parse_array(x)).tolist())

async def sin(x: NumericData) -> List[Any]:
    return to_serializable(np.sin(parse_array(x)).tolist())

async def cos(x: NumericData) -> List[Any]:
    return to_serializable(np.cos(parse_array(x)).tolist())

async def tan(x: NumericData) -> List[Any]:
    return to_serializable(np.tan(parse_array(x)).tolist())

async def rad2deg(x: NumericData) -> List[Any]:
    return to_serializable(np.rad2deg(parse_array(x)).tolist())

async def deg2rad(x: NumericData) -> List[Any]:
    return to_serializable(np.deg2rad(parse_array(x)).tolist())

async def clip(a: NumericData, a_min: float, a_max: float) -> List[Any]:
    return to_serializable(np.clip(parse_array(a), a_min, a_max).tolist())

async def round_val(a: NumericData, decimals: int = 0) -> List[Any]:
    return to_serializable(np.round(parse_array(a), decimals).tolist())

# ==========================================
# Aggregations
# ==========================================
async def sum_val(a: NumericData, axis: Optional[int] = None) -> Union[float, List[Any]]:
    res = np.sum(parse_array(a), axis=axis)
    return to_serializable(res.tolist())

async def prod(a: NumericData, axis: Optional[int] = None) -> Union[float, List[Any]]:
    res = np.prod(parse_array(a), axis=axis)
    return to_serializable(res.tolist())

async def cumsum(a: NumericData, axis: Optional[int] = None) -> List[Any]:
    res = np.cumsum(parse_array(a), axis=axis)
    return to_serializable(res.tolist())

async def cumprod(a: NumericData, axis: Optional[int] = None) -> List[Any]:
    res = np.cumprod(parse_array(a), axis=axis)
    return to_serializable(res.tolist())

async def diff(a: NumericData, n: int = 1, axis: int = -1) -> List[Any]:
    res = np.diff(parse_array(a), n=n, axis=axis)
    return to_serializable(res.tolist())

async def gradient(f: NumericData) -> List[Any]:
    res = np.gradient(parse_array(f))
    # Returns list of arrays if multi-dim input, or single array
    if isinstance(res, list):
        return [to_serializable(r.tolist()) for r in res]
    return to_serializable(res.tolist())

async def cross(a: NumericData, b: NumericData) -> List[Any]:
    return to_serializable(np.cross(parse_array(a), parse_array(b)).tolist())
