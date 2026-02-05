from mcp_servers.scipy_server.tools.core_ops import to_serializable, parse_data, NumericData
from scipy import ndimage
import numpy as np
from typing import Dict, Any, List

def _parse_img(data: Any) -> np.ndarray:
    return np.array(data)

async def img_gaussian(data: List[List[float]], sigma: float) -> List[List[float]]:
    """Gaussian filter."""
    arr = _parse_img(data)
    res = ndimage.gaussian_filter(arr, sigma=sigma)
    return to_serializable(res.tolist())

async def img_sobel(data: List[List[float]], axis: int = -1) -> List[List[float]]:
    """Sobel filter."""
    arr = _parse_img(data)
    res = ndimage.sobel(arr, axis=axis)
    return to_serializable(res.tolist())

async def img_laplace(data: List[List[float]]) -> List[List[float]]:
    """Laplace filter."""
    arr = _parse_img(data)
    res = ndimage.laplace(arr)
    return to_serializable(res.tolist())

async def img_median(data: List[List[float]], size: int = 3) -> List[List[float]]:
    """Median filter."""
    arr = _parse_img(data)
    res = ndimage.median_filter(arr, size=size)
    return to_serializable(res.tolist())

async def center_of_mass(data: List[List[float]]) -> List[float]:
    """Calculate center of mass."""
    arr = _parse_img(data)
    res = ndimage.center_of_mass(arr)
    return to_serializable(list(res))
