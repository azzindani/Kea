from mcp_servers.sklearn_server.tools.core_ops import parse_data, parse_vector, to_serializable, serialize_model, DataInput, VectorInput
from sklearn.ensemble import (
    RandomForestClassifier, RandomForestRegressor,
    GradientBoostingClassifier, GradientBoostingRegressor,
    AdaBoostClassifier, ExtraTreesClassifier, VotingClassifier
)
import pandas as pd
from typing import Dict, Any, List, Optional

async def _train_ensemble(model, X, y):
    X_df = parse_data(X)
    y_vec = parse_vector(y)
    model.fit(X_df, y_vec)
    score = model.score(X_df, y_vec)
    
    # Feature importances if available
    importances = model.feature_importances_.tolist() if hasattr(model, 'feature_importances_') else None
    
    return to_serializable({
        "train_score": score,
        "feature_importances": importances,
        "model": serialize_model(model)
    })

async def random_forest_clf(X: DataInput, y: VectorInput, n_estimators: int = 100) -> Dict[str, Any]:
    return await _train_ensemble(RandomForestClassifier(n_estimators=n_estimators, random_state=42), X, y)

async def random_forest_reg(X: DataInput, y: VectorInput, n_estimators: int = 100) -> Dict[str, Any]:
    return await _train_ensemble(RandomForestRegressor(n_estimators=n_estimators, random_state=42), X, y)

async def gradient_boosting_clf(X: DataInput, y: VectorInput, n_estimators: int = 100, learning_rate: float = 0.1) -> Dict[str, Any]:
    return await _train_ensemble(GradientBoostingClassifier(n_estimators=n_estimators, learning_rate=learning_rate, random_state=42), X, y)

async def gradient_boosting_reg(X: DataInput, y: VectorInput, n_estimators: int = 100, learning_rate: float = 0.1) -> Dict[str, Any]:
    return await _train_ensemble(GradientBoostingRegressor(n_estimators=n_estimators, learning_rate=learning_rate, random_state=42), X, y)

async def adaboost_clf(X: DataInput, y: VectorInput, n_estimators: int = 50) -> Dict[str, Any]:
    return await _train_ensemble(AdaBoostClassifier(n_estimators=n_estimators, random_state=42), X, y)
