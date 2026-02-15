from typing import Dict, Any, List, Optional
import pandas as pd
import structlog
from sklearn.ensemble import BaggingClassifier, BaggingRegressor, ExtraTreesClassifier, ExtraTreesRegressor, VotingClassifier, VotingRegressor, StackingClassifier, StackingRegressor, IsolationForest
from sklearn.feature_selection import SelectKBest, SelectPercentile, RFE, VarianceThreshold, chi2, f_classif, mutual_info_classif
from sklearn.impute import SimpleImputer
import numpy as np

logger = structlog.get_logger()

# --- Ensemble ---
def _ensemble(model, data_url, target_col) -> Dict[str, Any]:
    try:
        df = pd.read_csv(data_url)
        X = df.drop(columns=[target_col])
        # Simple imputation for robustness
        X = pd.get_dummies(X)
        X = pd.DataFrame(SimpleImputer().fit_transform(X), columns=X.columns)
        y = df[target_col]
        
        model.fit(X, y)
        return {"status": "trained", "params": str(model.get_params())}
    except Exception as e:
        return {"error": str(e)}

def ensemble_bagging_classifier(data_url: str, target_col: str, n_estimators: int = 10) -> Dict[str, Any]:
    """TRAINS Bagging Classifier. [DATA]"""
    return _ensemble(BaggingClassifier(n_estimators=n_estimators), data_url, target_col)

def ensemble_bagging_regressor(data_url: str, target_col: str, n_estimators: int = 10) -> Dict[str, Any]:
    """TRAINS Bagging Regressor. [DATA]"""
    return _ensemble(BaggingRegressor(n_estimators=n_estimators), data_url, target_col)

def ensemble_extra_trees_classifier(data_url: str, target_col: str, n_estimators: int = 100) -> Dict[str, Any]:
    """TRAINS Extra Trees Classifier. [DATA]"""
    return _ensemble(ExtraTreesClassifier(n_estimators=n_estimators), data_url, target_col)

def ensemble_extra_trees_regressor(data_url: str, target_col: str, n_estimators: int = 100) -> Dict[str, Any]:
    """TRAINS Extra Trees Regressor. [DATA]"""
    return _ensemble(ExtraTreesRegressor(n_estimators=n_estimators), data_url, target_col)

def ensemble_isolation_forest(data_url: str, contamination: float = 0.1) -> Dict[str, Any]:
    """TRAINS Isolation Forest (Anomaly). [DATA]"""
    try:
        df = pd.read_csv(data_url)
        X = pd.get_dummies(df.select_dtypes(include=['number']))
        X = SimpleImputer().fit_transform(X)
        model = IsolationForest(contamination=contamination)
        preds = model.fit_predict(X)
        return {"anomalies_detected": int((preds == -1).sum())}
    except Exception as e:
        return {"error": str(e)}

# --- Feature Selection ---
def select_k_best(data_url: str, target_col: str, k: int = 10) -> Dict[str, Any]:
    """SELECTS K Best Features. [DATA]"""
    try:
        df = pd.read_csv(data_url)
        X = df.drop(columns=[target_col])
        X = pd.get_dummies(X)
        X = SimpleImputer().fit_transform(X)
        y = df[target_col]
        
        selector = SelectKBest(score_func=f_classif, k=k) # Default f_classif
        selector.fit(X, y)
        mask = selector.get_support()
        # feature_names_in_ only in newer sklearn versions if dataframe passed, 
        # but imputer returns numpy array. Need to map back.
        # Actually passed X to imputer, lost col names.
        # Reconstruct roughly? Or just return indices.
        return {"selected_indices": [int(i) for i in np.where(mask)[0]]}
    except Exception as e:
        return {"error": str(e)}


def select_percentile(data_url: str, target_col: str, percentile: int = 10) -> Dict[str, Any]:
    """SELECTS Top Percentile Features. [DATA]"""
    try:
        df = pd.read_csv(data_url)
        X = df.drop(columns=[target_col]).select_dtypes(include=['number'])
        X = SimpleImputer().fit_transform(X)
        y = df[target_col]
        selector = SelectPercentile(score_func=f_classif, percentile=percentile)
        selector.fit(X, y)
        mask = selector.get_support()
        return {"selected_indices": [int(i) for i in np.where(mask)[0]]}
    except Exception as e:
        return {"error": str(e)}

def select_variance_threshold(data_url: str, threshold: float = 0.0) -> Dict[str, Any]:
    """SELECTS Features by Variance. [DATA]"""
    try:
        df = pd.read_csv(data_url).select_dtypes(include=['number'])
        selector = VarianceThreshold(threshold=threshold)
        selector.fit(df)
        mask = selector.get_support()
        return {"selected_indices": [int(i) for i in np.where(mask)[0]], "original_cols": list(df.columns)}
    except Exception as e:
        return {"error": str(e)}
