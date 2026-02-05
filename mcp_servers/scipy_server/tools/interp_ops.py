from mcp_servers.scipy_server.tools.core_ops import parse_data, to_serializable, NumericData
from scipy import interpolate
import numpy as np
from typing import Dict, Any, List, Optional

async def interp_1d(x: NumericData, y: NumericData, x_new: NumericData, kind: str = 'linear') -> List[float]:
    """
    1D Interpolation.
    kind: linear, nearest, nearest-up, zero, slinear, quadratic, cubic, previous, next
    """
    x_arr = parse_data(x)
    y_arr = parse_data(y)
    x_new_arr = parse_data(x_new)
    
    f = interpolate.interp1d(x_arr, y_arr, kind=kind, fill_value="extrapolate")
    y_new = f(x_new_arr)
    
    return to_serializable(y_new.tolist())

async def interp_spline(x: NumericData, y: NumericData, x_new: NumericData, k: int = 3, s: float = 0) -> List[float]:
    """
    Univariate Spline Interpolation.
    k: Degree of smoothing spline (1-5).
    s: Smoothing factor.
    """
    x_arr = parse_data(x)
    y_arr = parse_data(y)
    x_new_arr = parse_data(x_new)
    
    # Sort x if needed required for UnivariateSpline
    idx = np.argsort(x_arr)
    x_sorted = x_arr[idx]
    y_sorted = y_arr[idx]
    
    spl = interpolate.UnivariateSpline(x_sorted, y_sorted, k=k, s=s)
    y_new = spl(x_new_arr)
    
    return to_serializable(y_new.tolist())

async def grid_data(points: List[List[float]], values: NumericData, xi: List[List[float]], method: str = 'linear') -> List[float]:
    """
    Interpolate unstructured D-dimensional data.
    method: linear, nearest, cubic
    """
    pts = np.array(points)
    vals = parse_data(values)
    xi_arr = np.array(xi)
    
    res = interpolate.griddata(pts, vals, xi_arr, method=method)
    # Handle NaNs if any (convert to None or 0 or keep NaN string)
    # JSON doesn't support NaN, so we replace with None usually, or text "NaN"
    # to_serializable handles basic types but np.nan needs care. 
    # Let's replace nan with None
    res_list = res.tolist()
    return [None if np.isnan(v) else v for v in res_list]
