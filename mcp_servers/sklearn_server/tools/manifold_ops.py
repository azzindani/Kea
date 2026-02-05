from mcp_servers.sklearn_server.tools.core_ops import parse_data, to_serializable, serialize_model, DataInput
from sklearn.manifold import Isomap, LocallyLinearEmbedding, MDS, SpectralEmbedding
import pandas as pd
from typing import Dict, Any, List, Optional

async def isomap(X: DataInput, n_components: int = 2, n_neighbors: int = 5) -> Dict[str, Any]:
    """Isomap Embedding."""
    X_df = parse_data(X)
    model = Isomap(n_components=n_components, n_neighbors=n_neighbors)
    transformed = model.fit_transform(X_df)
    return to_serializable({
        "transformed": transformed.tolist(),
        "model": serialize_model(model)
    })

async def lle(X: DataInput, n_components: int = 2, n_neighbors: int = 5, method: str = 'standard') -> Dict[str, Any]:
    """Locally Linear Embedding."""
    X_df = parse_data(X)
    model = LocallyLinearEmbedding(n_components=n_components, n_neighbors=n_neighbors, method=method, random_state=42)
    transformed = model.fit_transform(X_df)
    return to_serializable({
        "transformed": transformed.tolist(),
        "reconstruction_error": model.reconstruction_error_,
        "model": serialize_model(model)
    })

async def mds(X: DataInput, n_components: int = 2, metric: bool = True) -> Dict[str, Any]:
    """Multi-dimensional Scaling."""
    X_df = parse_data(X)
    model = MDS(n_components=n_components, metric=metric, random_state=42, normalized_stress='auto')
    transformed = model.fit_transform(X_df)
    return to_serializable({
        "transformed": transformed.tolist(),
        "stress": model.stress_,
        "model": serialize_model(model)
    })

async def spectral_embedding(X: DataInput, n_components: int = 2) -> Dict[str, Any]:
    """Spectral Embedding (Laplacian Eigenmaps)."""
    X_df = parse_data(X)
    model = SpectralEmbedding(n_components=n_components, random_state=42)
    transformed = model.fit_transform(X_df)
    return to_serializable({
        "transformed": transformed.tolist(),
        "model": serialize_model(model)
    })
