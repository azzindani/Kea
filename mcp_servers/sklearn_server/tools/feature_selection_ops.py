from mcp_servers.sklearn_server.tools.core_ops import parse_data, parse_vector, to_serializable, serialize_model, DataInput, VectorInput
from sklearn.feature_selection import (
    SelectKBest, SelectPercentile, RFE, SelectFromModel, VarianceThreshold,
    chi2, f_classif, f_regression
)
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, Lasso
import pandas as pd
from typing import Dict, Any, List, Optional

async def select_k_best(X: DataInput, y: VectorInput, k: int = 10, score_func: str = 'f_classif') -> Dict[str, Any]:
    X_df = parse_data(X)
    y_vec = parse_vector(y)
    
    if score_func == 'chi2':
        func = chi2
    elif score_func == 'f_classif':
        func = f_classif
    elif score_func == 'f_regression':
        func = f_regression
    else:
        raise ValueError(f"Unknown score function: {score_func}")
        
    model = SelectKBest(score_func=func, k=k)
    transformed = model.fit_transform(X_df, y_vec)
    
    # Get selected feature names if possible
    selected_mask = model.get_support()
    selected_features = X_df.columns[selected_mask].tolist() if hasattr(X_df, 'columns') else []
    
    return to_serializable({
        "transformed": transformed.tolist(),
        "scores": model.scores_.tolist(),
        "selected_features": selected_features,
        "model": serialize_model(model)
    })

async def select_percentile(X: DataInput, y: VectorInput, percentile: int = 10, score_func: str = 'f_classif') -> Dict[str, Any]:
    X_df = parse_data(X)
    y_vec = parse_vector(y)
    
    if score_func == 'chi2':
        func = chi2
    elif score_func == 'f_classif':
        func = f_classif
    elif score_func == 'f_regression':
        func = f_regression
    else:
        raise ValueError(f"Unknown score function: {score_func}")

    model = SelectPercentile(score_func=func, percentile=percentile)
    transformed = model.fit_transform(X_df, y_vec)
    selected_mask = model.get_support()
    selected_features = X_df.columns[selected_mask].tolist() if hasattr(X_df, 'columns') else []

    return to_serializable({
        "transformed": transformed.tolist(),
        "scores": model.scores_.tolist(),
        "selected_features": selected_features,
        "model": serialize_model(model)
    })

async def rfe(X: DataInput, y: VectorInput, n_features_to_select: int = 5, estimator_type: str = 'random_forest_clf') -> Dict[str, Any]:
    X_df = parse_data(X)
    y_vec = parse_vector(y)
    
    if estimator_type == 'random_forest_clf':
        est = RandomForestClassifier(random_state=42)
    elif estimator_type == 'random_forest_reg':
        est = RandomForestRegressor(random_state=42)
    elif estimator_type == 'logistic_regression':
        est = LogisticRegression(max_iter=1000)
    elif estimator_type == 'lasso':
        est = Lasso()
    else:
        raise ValueError(f"Unknown estimator type: {estimator_type}")
        
    model = RFE(estimator=est, n_features_to_select=n_features_to_select)
    transformed = model.fit_transform(X_df, y_vec)
    selected_mask = model.get_support()
    selected_features = X_df.columns[selected_mask].tolist() if hasattr(X_df, 'columns') else []
    
    return to_serializable({
        "transformed": transformed.tolist(),
        "ranking": model.ranking_.tolist(),
        "selected_features": selected_features,
        "model": serialize_model(model)
    })

async def variance_threshold(X: DataInput, threshold: float = 0.0) -> Dict[str, Any]:
    X_df = parse_data(X)
    model = VarianceThreshold(threshold=threshold)
    transformed = model.fit_transform(X_df)
    selected_mask = model.get_support()
    selected_features = X_df.columns[selected_mask].tolist() if hasattr(X_df, 'columns') else []
    
    return to_serializable({
        "transformed": transformed.tolist(),
        "variances": model.variances_.tolist(),
        "selected_features": selected_features,
        "model": serialize_model(model)
    })
