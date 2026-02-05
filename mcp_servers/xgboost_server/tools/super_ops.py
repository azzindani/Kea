from mcp_servers.xgboost_server.tools.core_ops import parse_data_frame, parse_vector, serialize_booster, DataInput, VectorInput
from xgboost import XGBClassifier, XGBRegressor
from sklearn.model_selection import RandomizedSearchCV, GridSearchCV
import numpy as np
import scipy.stats as stats
from typing import Dict, Any, List, Optional

async def auto_xgboost_clf(X: DataInput, y: VectorInput, n_iter: int = 10, cv: int = 3, scoring: str = 'accuracy') -> Dict[str, Any]:
    """Auto-tune XGBClassifier using RandomizedSearchCV."""
    X_df = parse_data_frame(X)
    y_vec = parse_vector(y)
    
    param_dist = {
        'n_estimators': stats.randint(50, 200),
        'learning_rate': stats.uniform(0.01, 0.3),
        'subsample': stats.uniform(0.6, 0.4),
        'max_depth': stats.randint(3, 10),
        'colsample_bytree': stats.uniform(0.6, 0.4),
        'min_child_weight': stats.randint(1, 6)
    }
    
    clf = XGBClassifier(use_label_encoder=False, eval_metric='logloss')
    search = RandomizedSearchCV(clf, param_distributions=param_dist, n_iter=n_iter, cv=cv, scoring=scoring, random_state=42, n_jobs=1)
    search.fit(X_df, y_vec)
    
    return {
        "best_params": search.best_params_,
        "best_score": search.best_score_,
        "model": serialize_booster(search.best_estimator_)
    }

async def auto_xgboost_reg(X: DataInput, y: VectorInput, n_iter: int = 10, cv: int = 3, scoring: str = 'neg_mean_squared_error') -> Dict[str, Any]:
    """Auto-tune XGBRegressor using RandomizedSearchCV."""
    X_df = parse_data_frame(X)
    y_vec = parse_vector(y)
    
    param_dist = {
        'n_estimators': stats.randint(50, 200),
        'learning_rate': stats.uniform(0.01, 0.3),
        'subsample': stats.uniform(0.6, 0.4),
        'max_depth': stats.randint(3, 10),
        'colsample_bytree': stats.uniform(0.6, 0.4),
        'min_child_weight': stats.randint(1, 6)
    }
    
    clf = XGBRegressor()
    search = RandomizedSearchCV(clf, param_distributions=param_dist, n_iter=n_iter, cv=cv, scoring=scoring, random_state=42, n_jobs=1)
    search.fit(X_df, y_vec)
    
    return {
        "best_params": search.best_params_,
        "best_score": search.best_score_,
        "model": serialize_booster(search.best_estimator_)
    }
