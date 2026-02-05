from mcp_servers.sklearn_server.tools.core_ops import parse_data, parse_vector, to_serializable, serialize_model, DataInput, VectorInput
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.svm import SVR
from sklearn.tree import DecisionTreeRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neural_network import MLPRegressor
import pandas as pd
from typing import Dict, Any, List, Optional

async def _train_regressor(model, X, y):
    X_df = parse_data(X)
    y_vec = parse_vector(y)
    model.fit(X_df, y_vec)
    score = model.score(X_df, y_vec) # R2 score
    return to_serializable({
        "train_r2": score,
        "model": serialize_model(model)
    })

async def linear_regression(X: DataInput, y: VectorInput) -> Dict[str, Any]:
    return await _train_regressor(LinearRegression(), X, y)

async def ridge_regression(X: DataInput, y: VectorInput, alpha: float = 1.0) -> Dict[str, Any]:
    return await _train_regressor(Ridge(alpha=alpha), X, y)

async def lasso_regression(X: DataInput, y: VectorInput, alpha: float = 1.0) -> Dict[str, Any]:
    return await _train_regressor(Lasso(alpha=alpha), X, y)

async def elasticnet(X: DataInput, y: VectorInput, alpha: float = 1.0, l1_ratio: float = 0.5) -> Dict[str, Any]:
    return await _train_regressor(ElasticNet(alpha=alpha, l1_ratio=l1_ratio), X, y)

async def svr(X: DataInput, y: VectorInput, C: float = 1.0, kernel: str = 'rbf') -> Dict[str, Any]:
    return await _train_regressor(SVR(C=C, kernel=kernel), X, y)

async def decision_tree_reg(X: DataInput, y: VectorInput, max_depth: Optional[int] = None) -> Dict[str, Any]:
    return await _train_regressor(DecisionTreeRegressor(max_depth=max_depth), X, y)

async def knn_regressor(X: DataInput, y: VectorInput, n_neighbors: int = 5) -> Dict[str, Any]:
    return await _train_regressor(KNeighborsRegressor(n_neighbors=n_neighbors), X, y)

async def mlp_regressor(X: DataInput, y: VectorInput, hidden_layer_sizes: List[int] = [100]) -> Dict[str, Any]:
    return await _train_regressor(MLPRegressor(hidden_layer_sizes=tuple(hidden_layer_sizes)), X, y)
