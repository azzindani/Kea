from mcp_servers.numpy_server.tools.core_ops import parse_array, to_serializable, NumericData
import numpy as np
from typing import Dict, Any, List, Optional, Union

async def unique_counts(ar: NumericData) -> Dict[str, Any]:
    """Find the unique elements of an array and their counts."""
    vals, counts = np.unique(parse_array(ar), return_counts=True)
    return to_serializable({
        "values": vals.tolist(),
        "counts": counts.tolist()
    })

async def union1d(ar1: NumericData, ar2: NumericData) -> List[Any]:
    """Find the union of two arrays."""
    return to_serializable(np.union1d(parse_array(ar1), parse_array(ar2)).tolist())

async def intersect1d(ar1: NumericData, ar2: NumericData) -> List[Any]:
    """Find the intersection of two arrays."""
    return to_serializable(np.intersect1d(parse_array(ar1), parse_array(ar2)).tolist())

async def setdiff1d(ar1: NumericData, ar2: NumericData) -> List[Any]:
    """Find the set difference of two arrays."""
    return to_serializable(np.setdiff1d(parse_array(ar1), parse_array(ar2)).tolist())

async def setxor1d(ar1: NumericData, ar2: NumericData) -> List[Any]:
    """Find the set exclusive-or of two arrays."""
    return to_serializable(np.setxor1d(parse_array(ar1), parse_array(ar2)).tolist())

async def isin(element: NumericData, test_elements: NumericData) -> List[bool]:
    """Calculates element in test_elements, broadcasting over element only."""
    return to_serializable(np.isin(parse_array(element), parse_array(test_elements)).tolist())
