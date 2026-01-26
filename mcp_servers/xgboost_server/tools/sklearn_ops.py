from mcp_servers.xgboost_server.tools.core_ops import parse_data_frame, parse_vector, serialize_booster, DataInput, VectorInput
from xgboost import XGBClassifier, XGBRegressor, XGBRanker, XGBRFClassifier, XGBRFRegressor
from typing import Dict, Any, List, Optional, Union

async def _train_sklearn_model(model, X, y, sample_weight=None):
    X_df = parse_data_frame(X)
    y_vec = parse_vector(y)
    w_vec = parse_vector(sample_weight)
    
    model.fit(X_df, y_vec, sample_weight=w_vec)
    
    # Try getting score
    try:
        score = float(model.score(X_df, y_vec))
    except:
        score = None
        
    return {
        "score": score,
        "feature_importances": model.feature_importances_.tolist() if hasattr(model, 'feature_importances_') else None,
        "model": serialize_booster(model)
    }

async def xgb_classifier(X: DataInput, y: VectorInput, n_estimators: int = 100, learning_rate: float = 0.3, max_depth: int = 6, objective: str = 'binary:logistic', sample_weight: Optional[VectorInput] = None) -> Dict[str, Any]:
    """Train XGBClassifier."""
    model = XGBClassifier(
        n_estimators=n_estimators, learning_rate=learning_rate, max_depth=max_depth, 
        objective=objective, use_label_encoder=False, eval_metric='logloss'
    )
    return await _train_sklearn_model(model, X, y, sample_weight)

async def xgb_regressor(X: DataInput, y: VectorInput, n_estimators: int = 100, learning_rate: float = 0.3, max_depth: int = 6, objective: str = 'reg:squarederror', sample_weight: Optional[VectorInput] = None) -> Dict[str, Any]:
    """Train XGBRegressor."""
    model = XGBRegressor(
        n_estimators=n_estimators, learning_rate=learning_rate, max_depth=max_depth,
        objective=objective
    )
    return await _train_sklearn_model(model, X, y, sample_weight)

async def xgb_ranker(X: DataInput, y: VectorInput, group: VectorInput, n_estimators: int = 100, learning_rate: float = 0.1, objective: str = 'rank:pairwise') -> Dict[str, Any]:
    """Train XGBRanker. Needs 'group' information."""
    X_df = parse_data_frame(X)
    y_vec = parse_vector(y)
    group_vec = parse_vector(group)
    
    model = XGBRanker(
        n_estimators=n_estimators, learning_rate=learning_rate, 
        objective=objective
    )
    model.fit(X_df, y_vec, group=group_vec)
    
    return {
        "feature_importances": model.feature_importances_.tolist(),
        "model": serialize_booster(model)
    }

async def xgb_rf_classifier(X: DataInput, y: VectorInput, n_estimators: int = 100, max_depth: int = 6) -> Dict[str, Any]:
    """Train XGBRFClassifier (Random Forest)."""
    model = XGBRFClassifier(n_estimators=n_estimators, max_depth=max_depth, use_label_encoder=False, eval_metric='logloss')
    return await _train_sklearn_model(model, X, y)

async def xgb_rf_regressor(X: DataInput, y: VectorInput, n_estimators: int = 100, max_depth: int = 6) -> Dict[str, Any]:
    """Train XGBRFRegressor (Random Forest)."""
    model = XGBRFRegressor(n_estimators=n_estimators, max_depth=max_depth)
    return await _train_sklearn_model(model, X, y)
