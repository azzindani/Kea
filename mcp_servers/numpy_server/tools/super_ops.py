from mcp_servers.numpy_server.tools.core_ops import parse_array, to_serializable, NumericData
import numpy as np
from typing import Dict, Any, List

async def analyze_array(data: NumericData) -> Dict[str, Any]:
    """
    Super Tool: Full array analysis/profiling.
    """
    arr = parse_array(data)
    
    analysis = {
        "shape": arr.shape,
        "ndim": arr.ndim,
        "size": arr.size,
        "dtype": str(arr.dtype),
        "min": float(np.min(arr)) if arr.size > 0 else None,
        "max": float(np.max(arr)) if arr.size > 0 else None,
        "mean": float(np.mean(arr)) if arr.size > 0 else None,
        "std": float(np.std(arr)) if arr.size > 0 else None,
        "sparsity": float(np.count_nonzero(arr) / arr.size) if arr.size > 0 else 0.0,
        "nbytes": int(arr.nbytes)
    }
    
    return to_serializable(analysis)

async def matrix_dashboard(data: NumericData) -> Dict[str, Any]:
    """
    Super Tool: Comprehensive linear algebra report for a matrix.
    """
    arr = parse_array(data)
    if arr.ndim != 2:
        return {"error": "Input must be 2D matrix"}
    
    res = {
        "shape": arr.shape,
        "rank": int(np.linalg.matrix_rank(arr)),
        "trace": float(np.trace(arr)),
        "is_square": arr.shape[0] == arr.shape[1],
        "norm_fro": float(np.linalg.norm(arr))
    }
    
    if res["is_square"]:
        try:
            res["determinant"] = float(np.linalg.det(arr))
            res["condition_number"] = float(np.linalg.cond(arr))
            eigvals = np.linalg.eigvals(arr)
            # just magnitude for simplicity
            res["eigenvalues_abs"] = np.abs(eigvals).tolist()
        except np.linalg.LinAlgError:
            res["singular"] = True
            
    return to_serializable(res)

async def compare_arrays(a: NumericData, b: NumericData) -> Dict[str, Any]:
    """
    Super Tool: Deep comparison between two arrays.
    """
    arr1 = parse_array(a)
    arr2 = parse_array(b)
    
    if arr1.shape != arr2.shape:
        return {"error": f"Shapes mismatch: {arr1.shape} vs {arr2.shape}"}
    
    diff = arr1 - arr2
    mae = float(np.mean(np.abs(diff)))
    mse = float(np.mean(diff ** 2))
    max_diff = float(np.max(np.abs(diff)))
    is_close = bool(np.allclose(arr1, arr2))
    
    # Correlation (flattened)
    if arr1.size > 1:
        corr = float(np.corrcoef(arr1.flatten(), arr2.flatten())[0, 1])
    else:
        corr = None
        
    return {
        "is_close": is_close,
        "mae": mae,
        "mse": mse,
        "max_diff": max_diff,
        "correlation": corr
    }
