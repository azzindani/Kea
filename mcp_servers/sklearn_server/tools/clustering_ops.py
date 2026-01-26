from mcp_servers.sklearn_server.tools.core_ops import parse_data, to_serializable, serialize_model, DataInput
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering, MeanShift, AffinityPropagation, SpectralClustering
import pandas as pd
from typing import Dict, Any, List, Optional

async def kmeans(X: DataInput, n_clusters: int = 8) -> Dict[str, Any]:
    X_df = parse_data(X)
    model = KMeans(n_clusters=n_clusters, random_state=42)
    labels = model.fit_predict(X_df)
    return to_serializable({
        "labels": labels.tolist(),
        "inertia": model.inertia_,
        "centers": model.cluster_centers_.tolist(),
        "model": serialize_model(model)
    })

async def dbscan(X: DataInput, eps: float = 0.5, min_samples: int = 5) -> Dict[str, Any]:
    X_df = parse_data(X)
    model = DBSCAN(eps=eps, min_samples=min_samples)
    labels = model.fit_predict(X_df)
    return to_serializable({
        "labels": labels.tolist(),
        "model": serialize_model(model)
    })

async def agglomerative(X: DataInput, n_clusters: int = 2) -> Dict[str, Any]:
    X_df = parse_data(X)
    model = AgglomerativeClustering(n_clusters=n_clusters)
    labels = model.fit_predict(X_df)
    return to_serializable({
        "labels": labels.tolist(),
        "model": serialize_model(model)
    })

async def spectral_clustering(X: DataInput, n_clusters: int = 8) -> Dict[str, Any]:
    X_df = parse_data(X)
    model = SpectralClustering(n_clusters=n_clusters, random_state=42)
    labels = model.fit_predict(X_df)
    return to_serializable({
        "labels": labels.tolist(),
        "model": serialize_model(model)
    })
