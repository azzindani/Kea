from mcp_servers.sklearn_server.tools.core_ops import parse_data, parse_vector, to_serializable, serialize_model, DataInput, VectorInput
from sklearn.gaussian_process import GaussianProcessClassifier, GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C
import pandas as pd
from typing import Dict, Any, List, Optional

async def gaussian_process_clf(X: DataInput, y: VectorInput) -> Dict[str, Any]:
    """Gaussian Process Classifier (Probabilistic)."""
    X_df = parse_data(X)
    y_vec = parse_vector(y)
    
    # Default Kernel
    kernel = 1.0 * RBF(1.0)
    model = GaussianProcessClassifier(kernel=kernel, random_state=42)
    model.fit(X_df, y_vec)
    
    return to_serializable({
        "train_score": model.score(X_df, y_vec),
        "kernel_params": model.kernel_.get_params(),
        "model": serialize_model(model)
    })

async def gaussian_process_reg(X: DataInput, y: VectorInput) -> Dict[str, Any]:
    """Gaussian Process Regressor (Kriging)."""
    X_df = parse_data(X)
    y_vec = parse_vector(y)
    
    kernel = C(1.0, (1e-3, 1e3)) * RBF(10, (1e-2, 1e2))
    model = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=5, random_state=42)
    model.fit(X_df, y_vec)
    
    return to_serializable({
        "train_score": model.score(X_df, y_vec),
        "kernel_params": model.kernel_.get_params(),
        "model": serialize_model(model)
    })
