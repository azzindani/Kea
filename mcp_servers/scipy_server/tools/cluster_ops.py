from mcp_servers.scipy_server.tools.core_ops import parse_data, to_serializable, NumericData
from scipy.cluster import vq, hierarchy
from scipy.spatial.distance import pdist
import numpy as np
from typing import Dict, Any, List

# ==========================================
# Vector Quantization / K-Means
# ==========================================
async def kmeans(data: List[List[float]], k_or_guess: Any) -> Dict[str, Any]:
    """
    K-Means clustering.
    k_or_guess: number of centroids OR array of initial centroids.
    """
    obs = np.array(data)
    # Whiten data first is usually recommended for scipy.cluster.vq
    # We will assume user provides raw data, we can whiten inside or separate tool.
    # Let's stick to raw kmeans2 for simplicity or vq.kmeans
    
    # Using kmeans2 for centroids and labels
    centroid, label = vq.kmeans2(obs, k_or_guess, minit='points')
    
    return to_serializable({
        "centroids": centroid.tolist(),
        "labels": label.tolist()
    })

async def whitening(data: List[List[float]]) -> List[List[float]]:
    """Normalize a group of observations on a per feature basis."""
    obs = np.array(data)
    res = vq.whiten(obs)
    return to_serializable(res.tolist())

# ==========================================
# Hierarchical Clustering
# ==========================================
async def linkage_matrix(data: List[List[float]], method: str = 'single', metric: str = 'euclidean') -> List[List[float]]:
    """
    Perform hierarchical/agglomerative clustering.
    Returns the linkage matrix (Z).
    """
    obs = np.array(data)
    # pdist calculation often implicit in linkage if raw data passed
    # scipy linkage accepts raw observations directly
    Z = hierarchy.linkage(obs, method=method, metric=metric)
    return to_serializable(Z.tolist())

async def fcluster(Z: List[List[float]], t: float, criterion: str = 'distance') -> List[int]:
    """
    Form flat clusters from the hierarchical clustering defined by the given linkage matrix.
    t: threshold
    """
    Z_arr = np.array(Z)
    res = hierarchy.fcluster(Z_arr, t, criterion=criterion)
    return to_serializable(res.tolist())
