from mcp_servers.xgboost_server.tools.core_ops import create_dmatrix, serialize_booster, DataInput, VectorInput
import xgboost as xgb
from typing import Dict, Any, List, Optional, Union

async def train_booster(X: DataInput, y: VectorInput, params: Dict[str, Any] = None, num_boost_round: int = 10, weight: Optional[VectorInput] = None) -> Dict[str, Any]:
    """Train a booster using native API."""
    if params is None:
        params = {'objective': 'reg:squarederror'}
        
    dtrain = create_dmatrix(X, y, weight)
    booster = xgb.train(params, dtrain, num_boost_round=num_boost_round)
    
    return {
        "model": serialize_booster(booster)
    }

async def cv_booster(X: DataInput, y: VectorInput, params: Dict[str, Any] = None, num_boost_round: int = 10, nfold: int = 3, stratified: bool = False, metrics: List[str] = ['rmse'], seed: int = 0) -> Dict[str, Any]:
    """Run Cross-Validation using native API."""
    if params is None:
        params = {'objective': 'reg:squarederror'}
        
    dtrain = create_dmatrix(X, y)
    
    # Returns DataFrame
    cv_results = xgb.cv(
        params, dtrain, num_boost_round=num_boost_round, 
        nfold=nfold, stratified=stratified, metrics=metrics, seed=seed
    )
    
    return {
        "cv_results": cv_results.to_dict(orient='list')
    }
