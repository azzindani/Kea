import pandas as pd
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
import xgboost as xgb
import structlog
from typing import List, Dict, Any, Optional

logger = structlog.get_logger()

def get_estimator(model_name: str, task: str):
    if model_name == 'xgboost':
        return xgb.XGBClassifier() if task == 'classifier' else xgb.XGBRegressor()
    elif model_name == 'rf':
        return RandomForestClassifier() if task == 'classifier' else RandomForestRegressor()
    elif model_name == 'svm':
        return SVC() if task == 'classifier' else None # SVM Regressor SVR could be added
    elif model_name == 'logistic':
        return LogisticRegression()
    # Default
    return RandomForestClassifier()

async def perform_grid_search(data_url: str, target_column: str, model_name: str, param_grid: Dict[str, List[Any]], cv: int = 5, task: str = 'classifier') -> Dict[str, Any]:
    """TUNES hyperparameters via Grid. [ACTION]
    
    [RAG Context]
    Exhaustive search over specified parameter values for an estimator.
    Args:
        model_name: 'xgboost', 'rf', 'svm', 'logistic'.
        param_grid: Dictionary with parameters names (str) as keys and lists of parameter settings to try.
    """
    try:
        df = pd.read_csv(data_url)
        X = df.drop(columns=[target_column])
        y = df[target_column]
        X = pd.get_dummies(X)
        
        estimator = get_estimator(model_name, task)
        
        grid_search = GridSearchCV(estimator, param_grid, cv=cv, n_jobs=-1, verbose=1)
        grid_search.fit(X, y)
        
        return {
            "best_params": grid_search.best_params_,
            "best_score": float(grid_search.best_score_),
            "best_estimator": str(grid_search.best_estimator_)
        }
        
    except Exception as e:
        logger.error("perform_grid_search failed", error=str(e))
        return {"error": str(e)}

async def perform_random_search(data_url: str, target_column: str, model_name: str, param_distributions: Dict[str, List[Any]], n_iter: int = 10, cv: int = 5, task: str = 'classifier') -> Dict[str, Any]:
    """TUNES hyperparameters via Random. [ACTION]
    
    [RAG Context]
    Randomized search on hyper parameters.
    Args:
        n_iter: Number of parameter settings that are sampled.
    """
    try:
        df = pd.read_csv(data_url)
        X = df.drop(columns=[target_column])
        y = df[target_column]
        X = pd.get_dummies(X)
        
        estimator = get_estimator(model_name, task)
        
        random_search = RandomizedSearchCV(estimator, param_distributions, n_iter=n_iter, cv=cv, n_jobs=-1, verbose=1, random_state=42)
        random_search.fit(X, y)
        
        return {
            "best_params": random_search.best_params_,
            "best_score": float(random_search.best_score_),
            "best_estimator": str(random_search.best_estimator_)
        }
        
    except Exception as e:
        logger.error("perform_random_search failed", error=str(e))
        return {"error": str(e)}
