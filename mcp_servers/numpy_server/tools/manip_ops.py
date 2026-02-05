from mcp_servers.numpy_server.tools.core_ops import parse_array, to_serializable, NumericData
import numpy as np
from typing import Dict, Any, List, Optional, Union

async def reshape(a: NumericData, newshape: List[int]) -> List[Any]:
    """Gives a new shape to an array without changing its data."""
    arr = parse_array(a)
    return to_serializable(arr.reshape(newshape).tolist())

async def flatten(a: NumericData) -> List[Any]:
    """Return a copy of the array collapsed into one dimension."""
    arr = parse_array(a)
    return to_serializable(arr.flatten().tolist())

async def transpose(a: NumericData, axes: Optional[List[int]] = None) -> List[Any]:
    """Reverse or permute the axes of an array."""
    arr = parse_array(a)
    return to_serializable(np.transpose(arr, axes).tolist())

async def flip(m: NumericData, axis: Optional[Union[int, List[int]]] = None) -> List[Any]:
    """Reverse the order of elements in an array along the given axis."""
    arr = parse_array(m)
    return to_serializable(np.flip(arr, axis).tolist())

async def roll(a: NumericData, shift: Union[int, List[int]], axis: Optional[Union[int, List[int]]] = None) -> List[Any]:
    """Roll array elements along a given axis."""
    arr = parse_array(a)
    return to_serializable(np.roll(arr, shift, axis=axis).tolist())

async def concatenate(arrays: List[NumericData], axis: int = 0) -> List[Any]:
    """Join a sequence of arrays along an existing axis."""
    # Need to parse each array
    parsed_arrays = [parse_array(a) for a in arrays]
    return to_serializable(np.concatenate(parsed_arrays, axis=axis).tolist())

async def stack(arrays: List[NumericData], axis: int = 0) -> List[Any]:
    """Join a sequence of arrays along a new axis."""
    parsed_arrays = [parse_array(a) for a in arrays]
    return to_serializable(np.stack(parsed_arrays, axis=axis).tolist())

async def vstack(tup: List[NumericData]) -> List[Any]:
    """Stack arrays in sequence vertically (row wise)."""
    parsed = [parse_array(a) for a in tup]
    return to_serializable(np.vstack(parsed).tolist())

async def hstack(tup: List[NumericData]) -> List[Any]:
    """Stack arrays in sequence horizontally (column wise)."""
    parsed = [parse_array(a) for a in tup]
    return to_serializable(np.hstack(parsed).tolist())

async def split(ary: NumericData, indices_or_sections: Union[int, List[int]], axis: int = 0) -> List[List[Any]]:
    """Split an array into multiple sub-arrays."""
    arr = parse_array(ary)
    res = np.split(arr, indices_or_sections, axis=axis)
    return [to_serializable(r.tolist()) for r in res]

async def tile(A: NumericData, reps: List[int]) -> List[Any]:
    """Construct an array by repeating A the number of times given by reps."""
    arr = parse_array(A)
    return to_serializable(np.tile(arr, reps).tolist())

async def repeat(a: NumericData, repeats: Union[int, List[int]], axis: Optional[int] = None) -> List[Any]:
    """Repeat elements of an array."""
    arr = parse_array(a)
    return to_serializable(np.repeat(arr, repeats, axis=axis).tolist())

async def unique(ar: NumericData) -> List[Any]:
    """Find the unique elements of an array."""
    arr = parse_array(ar)
    return to_serializable(np.unique(arr).tolist())

async def trim_zeros(filt: NumericData, trim: str = 'fb') -> List[Any]:
    """Trim the leading and/or trailing zeros from a 1-D array or sequence."""
    # trim_zeros wants 1D sequence usually
    arr = parse_array(filt)
    # usually needs 1D
    if arr.ndim > 1:
        arr = arr.flatten()
    return to_serializable(np.trim_zeros(arr, trim).tolist())

async def pad(array: NumericData, pad_width: List[Any], mode: str = 'constant', constant_values: Any = 0) -> List[Any]:
    """Pad an array."""
    arr = parse_array(array)
    return to_serializable(np.pad(arr, pad_width, mode=mode, constant_values=constant_values).tolist())
