from mcp_servers.scipy_server.tools.core_ops import to_serializable, parse_data, NumericData
from scipy import spatial
import numpy as np
from typing import Dict, Any, List

async def distance_euclidean(u: List[float], v: List[float]) -> float:
    """Euclidean distance."""
    return float(spatial.distance.euclidean(u, v))

async def distance_cosine(u: List[float], v: List[float]) -> float:
    """Cosine distance."""
    return float(spatial.distance.cosine(u, v))

async def distance_matrix(x: List[List[float]], y: List[List[float]]) -> List[List[float]]:
    """Compute distance matrix between two sets of points."""
    return to_serializable(spatial.distance_matrix(x, y).tolist())

async def convex_hull(points: List[List[float]]) -> Dict[str, Any]:
    """Compute Convex Hull of points (Area/Volume)."""
    arr = np.array(points)
    hull = spatial.ConvexHull(arr)
    return to_serializable({
        "area": hull.area,
        "volume": hull.volume,
        "vertices": hull.vertices.tolist()
    })
