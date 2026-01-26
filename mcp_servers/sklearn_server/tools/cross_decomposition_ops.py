from mcp_servers.sklearn_server.tools.core_ops import parse_data, parse_vector, to_serializable, serialize_model, DataInput, VectorInput
from sklearn.cross_decomposition import PLSRegression, CCA
import pandas as pd
from typing import Dict, Any, List, Optional

async def pls_regression(X: DataInput, Y: DataInput, n_components: int = 2) -> Dict[str, Any]:
    """Partial Least Squares Regression."""
    X_df = parse_data(X)
    Y_df = parse_data(Y) # PLS handles multidimensional Y
    
    model = PLSRegression(n_components=n_components)
    model.fit(X_df, Y_df)
    
    return to_serializable({
        "x_scores": model.x_scores_.tolist(),
        "y_scores": model.y_scores_.tolist(),
        "x_weights": model.x_weights_.tolist(),
        "model": serialize_model(model)
    })

async def cca(X: DataInput, Y: DataInput, n_components: int = 2) -> Dict[str, Any]:
    """Canonical Correlation Analysis."""
    X_df = parse_data(X)
    Y_df = parse_data(Y)
    
    model = CCA(n_components=n_components)
    model.fit(X_df, Y_df)
    
    return to_serializable({
        "x_scores": model.x_scores_.tolist(),
        "y_scores": model.y_scores_.tolist(),
        "model": serialize_model(model)
    })
