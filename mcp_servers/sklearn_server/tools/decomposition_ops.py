from mcp_servers.sklearn_server.tools.core_ops import parse_data, to_serializable, serialize_model, DataInput
from sklearn.decomposition import PCA, IncrementalPCA, NMF, FastICA, FactorAnalysis
from sklearn.manifold import TSNE
import pandas as pd
from typing import Dict, Any, List, Optional

async def pca(X: DataInput, n_components: int = 2) -> Dict[str, Any]:
    X_df = parse_data(X)
    model = PCA(n_components=n_components)
    transformed = model.fit_transform(X_df)
    return to_serializable({
        "transformed": transformed.tolist(),
        "explained_variance_ratio": model.explained_variance_ratio_.tolist(),
        "components": model.components_.tolist(),
        "model": serialize_model(model)
    })

async def tsne(X: DataInput, n_components: int = 2, perplexity: float = 30.0) -> Dict[str, Any]:
    X_df = parse_data(X)
    model = TSNE(n_components=n_components, perplexity=perplexity, random_state=42)
    transformed = model.fit_transform(X_df)
    return to_serializable({
        "transformed": transformed.tolist(),
        "model": serialize_model(model)
    })

async def nmf(X: DataInput, n_components: int = 2) -> Dict[str, Any]:
    X_df = parse_data(X)
    model = NMF(n_components=n_components, random_state=42)
    transformed = model.fit_transform(X_df)
    return to_serializable({
        "transformed": transformed.tolist(),
        "components": model.components_.tolist(),
        "model": serialize_model(model)
    })

async def fast_ica(X: DataInput, n_components: int = 2) -> Dict[str, Any]:
    X_df = parse_data(X)
    model = FastICA(n_components=n_components, random_state=42)
    transformed = model.fit_transform(X_df)
    return to_serializable({
        "transformed": transformed.tolist(),
        "model": serialize_model(model)
    })
