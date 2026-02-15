from typing import Dict, Any, List, Optional
import pandas as pd
import structlog
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering, SpectralClustering, OPTICS, Birch, MeanShift, AffinityPropagation

logger = structlog.get_logger()

def _cluster(model, data_url, drop_cols=None) -> Dict[str, Any]:
    try:
        df = pd.read_csv(data_url)
        if drop_cols:
            X = df.drop(columns=drop_cols)
        else:
            X = df.select_dtypes(include=['number'])
        
        labels = model.fit_predict(X)
        return {
            "labels": labels.tolist()[:100], # Limit output size
            "n_clusters": len(set(labels)) if hasattr(model, 'labels_') else None,
            "params": model.get_params()
        }
    except Exception as e:
        return {"error": str(e)}

def cluster_kmeans(data_url: str, n_clusters: int = 8, drop_cols: List[str] = None) -> Dict[str, Any]:
    """CLUSTERS data using K-Means. [DATA]"""
    return _cluster(KMeans(n_clusters=n_clusters), data_url, drop_cols)

def cluster_dbscan(data_url: str, eps: float = 0.5, min_samples: int = 5, drop_cols: List[str] = None) -> Dict[str, Any]:
    """CLUSTERS data using DBSCAN. [DATA]"""
    return _cluster(DBSCAN(eps=eps, min_samples=min_samples), data_url, drop_cols)

def cluster_agglomerative(data_url: str, n_clusters: int = 2, drop_cols: List[str] = None) -> Dict[str, Any]:
    """CLUSTERS data using Agglomerative Clustering. [DATA]"""
    return _cluster(AgglomerativeClustering(n_clusters=n_clusters), data_url, drop_cols)

def cluster_spectral(data_url: str, n_clusters: int = 8, drop_cols: List[str] = None) -> Dict[str, Any]:
    """CLUSTERS data using Spectral Clustering. [DATA]"""
    return _cluster(SpectralClustering(n_clusters=n_clusters), data_url, drop_cols)

def cluster_optics(data_url: str, min_samples: int = 5, drop_cols: List[str] = None) -> Dict[str, Any]:
    """CLUSTERS data using OPTICS. [DATA]"""
    return _cluster(OPTICS(min_samples=min_samples), data_url, drop_cols)

def cluster_birch(data_url: str, n_clusters: int = 3, drop_cols: List[str] = None) -> Dict[str, Any]:
    """CLUSTERS data using Birch. [DATA]"""
    return _cluster(Birch(n_clusters=n_clusters), data_url, drop_cols)

def cluster_meanshift(data_url: str, bandwidth: Optional[float] = None, drop_cols: List[str] = None) -> Dict[str, Any]:
    """CLUSTERS data using MeanShift. [DATA]"""
    return _cluster(MeanShift(bandwidth=bandwidth), data_url, drop_cols)

def cluster_affinity_propagation(data_url: str, damping: float = 0.5, drop_cols: List[str] = None) -> Dict[str, Any]:
    """CLUSTERS data using Affinity Propagation. [DATA]"""
    return _cluster(AffinityPropagation(damping=damping), data_url, drop_cols)
