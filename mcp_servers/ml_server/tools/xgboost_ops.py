import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, classification_report, mean_squared_error
import structlog
from typing import List, Dict, Any, Optional

logger = structlog.get_logger()

async def train_xgboost_model(data_url: str, target_column: str, model_type: str = "classifier", params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """TRAINS XGBoost model. [ACTION]
    
    [RAG Context]
    Trains an XGBoost model (Classifier or Regressor) on the provided dataset.
    Args:
        data_url: URL or path to CSV dataset.
        target_column: Name of the target variable.
        model_type: 'classifier' or 'regressor'.
        params: Dictionary of XGBoost parameters (learning_rate, max_depth, etc).
    """
    try:
        df = pd.read_csv(data_url)
        X = df.drop(columns=[target_column])
        y = df[target_column]
        
        # Handle categorical data via OneHotEnconding if needed, but XGBoost can handle some internals.
        # For robustness, we recommend numeric inputs or pre-processing, 
        # but here we'll use get_dummies for basic support
        X = pd.get_dummies(X)
        
        default_params = {
            'n_estimators': 100,
            'learning_rate': 0.1,
            'max_depth': 3,
            'random_state': 42
        }
        if params:
            default_params.update(params)
            
        if model_type == 'classifier':
            model = xgb.XGBClassifier(**default_params)
            model.fit(X, y)
            preds = model.predict(X)
            score = accuracy_score(y, preds)
            report = classification_report(y, preds, output_dict=True)
            return {
                "status": "trained",
                "accuracy": score,
                "report": report,
                "model_params": model.get_params()
            }
        else:
            model = xgb.XGBRegressor(**default_params)
            model.fit(X, y)
            preds = model.predict(X)
            mse = mean_squared_error(y, preds)
            return {
                "status": "trained",
                "mse": mse,
                "rmse": np.sqrt(mse),
                "model_params": model.get_params()
            }
            
    except Exception as e:
        logger.error("train_xgboost_model failed", error=str(e))
        return {"error": str(e)}

async def cross_validate_xgboost(data_url: str, target_column: str, cv: int = 5, model_type: str = "classifier") -> Dict[str, Any]:
    """VALIDATES XGBoost model. [DATA]
    
    [RAG Context]
    Performs K-Fold Cross-Validation on XGBoost model.
    Returns mean score and standard deviation.
    """
    try:
        df = pd.read_csv(data_url)
        X = df.drop(columns=[target_column])
        y = df[target_column]
        X = pd.get_dummies(X)
        
        if model_type == 'classifier':
            model = xgb.XGBClassifier()
            scoring = 'accuracy'
        else:
            model = xgb.XGBRegressor()
            scoring = 'neg_mean_squared_error'
            
        scores = cross_val_score(model, X, y, cv=cv, scoring=scoring)
        
        return {
            "cv_scores": scores.tolist(),
            "mean_score": float(scores.mean()),
            "std_dev": float(scores.std())
        }
        
    except Exception as e:
        logger.error("cross_validate_xgboost failed", error=str(e))
        return {"error": str(e)}

async def analyze_xgboost_importance(data_url: str, target_column: str, importance_type: str = "gain") -> Dict[str, Any]:
    """ANALYZES feature importance. [DATA]
    
    [RAG Context]
    Extracts feature importance from a trained XGBoost model.
    Args:
        importance_type: 'gain', 'weight', 'cover', 'total_gain', 'total_cover'.
    """
    try:
        df = pd.read_csv(data_url)
        X = df.drop(columns=[target_column])
        y = df[target_column]
        X = pd.get_dummies(X)
        
        model = xgb.XGBClassifier() # Default to classifier for importance check
        model.fit(X, y)
        
        importance = model.get_booster().get_score(importance_type=importance_type)
        # Sort by value DESC
        sorted_importance = dict(sorted(importance.items(), key=lambda item: item[1], reverse=True))
        
        return sorted_importance
        
    except Exception as e:
        logger.error("analyze_xgboost_importance failed", error=str(e))
        return {"error": str(e)}
