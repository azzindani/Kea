from mcp_servers.numpy_server.tools.core_ops import parse_array, to_serializable, NumericData
import numpy as np
from typing import Dict, Any, List, Optional, Union

async def bitwise_and(x1: NumericData, x2: NumericData) -> List[Any]:
    """Compute the bit-wise AND of two arrays element-wise."""
    return to_serializable(np.bitwise_and(parse_array(x1, dtype='int64'), parse_array(x2, dtype='int64')).tolist())

async def bitwise_or(x1: NumericData, x2: NumericData) -> List[Any]:
    """Compute the bit-wise OR of two arrays element-wise."""
    return to_serializable(np.bitwise_or(parse_array(x1, dtype='int64'), parse_array(x2, dtype='int64')).tolist())

async def bitwise_xor(x1: NumericData, x2: NumericData) -> List[Any]:
    """Compute the bit-wise XOR of two arrays element-wise."""
    return to_serializable(np.bitwise_xor(parse_array(x1, dtype='int64'), parse_array(x2, dtype='int64')).tolist())

async def bitwise_not(x: NumericData) -> List[Any]:
    """Compute bit-wise inversion, or bit-wise NOT, element-wise."""
    return to_serializable(np.bitwise_not(parse_array(x, dtype='int64')).tolist())

async def left_shift(x1: NumericData, x2: NumericData) -> List[Any]:
    """Shift the bits of an integer to the left."""
    return to_serializable(np.left_shift(parse_array(x1, dtype='int64'), parse_array(x2, dtype='int64')).tolist())

async def right_shift(x1: NumericData, x2: NumericData) -> List[Any]:
    """Shift the bits of an integer to the right."""
    return to_serializable(np.right_shift(parse_array(x1, dtype='int64'), parse_array(x2, dtype='int64')).tolist())

async def binary_repr(num: int, width: Optional[int] = None) -> str:
    """Return the binary representation of the input number as a string."""
    return str(np.binary_repr(num, width=width))
