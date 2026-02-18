import pandas as pd
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.svm import SVC, SVR
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, AdaBoostClassifier, AdaBoostRegressor, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge, Lasso
from sklearn.naive_bayes import GaussianNB, MultinomialNB
from sklearn.metrics import accuracy_score, mean_squared_error
import structlog
from typing import Dict, Any, Optional, List

logger = structlog.get_logger()

# Helper
def _train_and_evaluate(model, data_url, target_column, task='classification'):
    try:
        df = pd.read_csv(data_url)
        X = df.drop(columns=[target_column])
        y = df[target_column]
        X = pd.get_dummies(X) # Simple handled
        
        model.fit(X, y)
        preds = model.predict(X)
        
        if task == 'classification':
             score = accuracy_score(y, preds)
             metric = "accuracy"
        else:
             score = mean_squared_error(y, preds)
             metric = "mse"
             
        return {
            "status": "trained",
            metric: score,
            "params": model.get_params()
        }
    except Exception as e:
        logger.error(f"Training failed: {e}")
        return {"error": str(e)}

# --- 1. KNN ---
async def train_knn_classifier(data_url: str, target_column: str, n_neighbors: int = 5) -> Dict[str, Any]:
    """TRAINS K-Nearest Neighbors Classifier. [ACTION]"""
    return _train_and_evaluate(KNeighborsClassifier(n_neighbors=n_neighbors), data_url, target_column, 'classification')

async def train_knn_regressor(data_url: str, target_column: str, n_neighbors: int = 5) -> Dict[str, Any]:
    """TRAINS K-Nearest Neighbors Regressor. [ACTION]"""
    return _train_and_evaluate(KNeighborsRegressor(n_neighbors=n_neighbors), data_url, target_column, 'regression')

# --- 2. SVM ---
async def train_svm_classifier(data_url: str, target_column: str, kernel: str = 'rbf', C: float = 1.0) -> Dict[str, Any]:
    """TRAINS Support Vector Machine Classifier. [ACTION]"""
    return _train_and_evaluate(SVC(kernel=kernel, C=C), data_url, target_column, 'classification')

async def train_svm_regressor(data_url: str, target_column: str, kernel: str = 'rbf', C: float = 1.0) -> Dict[str, Any]:
    """TRAINS Support Vector Machine Regressor. [ACTION]"""
    return _train_and_evaluate(SVR(kernel=kernel, C=C), data_url, target_column, 'regression')

# --- 3. Decision Trees ---
async def train_decision_tree_classifier(data_url: str, target_column: str, max_depth: Optional[int] = None) -> Dict[str, Any]:
    """TRAINS Decision Tree Classifier. [ACTION]"""
    return _train_and_evaluate(DecisionTreeClassifier(max_depth=max_depth), data_url, target_column, 'classification')

async def train_decision_tree_regressor(data_url: str, target_column: str, max_depth: Optional[int] = None) -> Dict[str, Any]:
    """TRAINS Decision Tree Regressor. [ACTION]"""
    return _train_and_evaluate(DecisionTreeRegressor(max_depth=max_depth), data_url, target_column, 'regression')

# --- 4. Random Forest ---
async def train_random_forest_classifier(data_url: str, target_column: str, n_estimators: int = 100, max_depth: Optional[int] = None) -> Dict[str, Any]:
    """TRAINS Random Forest Classifier. [ACTION]"""
    return _train_and_evaluate(RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth), data_url, target_column, 'classification')

async def train_random_forest_regressor(data_url: str, target_column: str, n_estimators: int = 100, max_depth: Optional[int] = None) -> Dict[str, Any]:
    """TRAINS Random Forest Regressor. [ACTION]"""
    return _train_and_evaluate(RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth), data_url, target_column, 'regression')

# --- 5. Logistic/Linear ---
async def train_logistic_regression(data_url: str, target_column: str, C: float = 1.0) -> Dict[str, Any]:
    """TRAINS Logistic Regression. [ACTION]"""
    return _train_and_evaluate(LogisticRegression(C=C, max_iter=1000), data_url, target_column, 'classification')

async def train_linear_regression(data_url: str, target_column: str) -> Dict[str, Any]:
    """TRAINS Linear Regression. [ACTION]"""
    return _train_and_evaluate(LinearRegression(), data_url, target_column, 'regression')

async def train_ridge_regression(data_url: str, target_column: str, alpha: float = 1.0) -> Dict[str, Any]:
    """TRAINS Ridge Regression. [ACTION]"""
    return _train_and_evaluate(Ridge(alpha=alpha), data_url, target_column, 'regression')

async def train_lasso_regression(data_url: str, target_column: str, alpha: float = 1.0) -> Dict[str, Any]:
    """TRAINS Lasso Regression. [ACTION]"""
    return _train_and_evaluate(Lasso(alpha=alpha), data_url, target_column, 'regression')

# --- 6. Naive Bayes ---
async def train_gaussian_nb(data_url: str, target_column: str) -> Dict[str, Any]:
    """TRAINS Gaussian Naive Bayes. [ACTION]"""
    return _train_and_evaluate(GaussianNB(), data_url, target_column, 'classification')

async def train_multinomial_nb(data_url: str, target_column: str) -> Dict[str, Any]:
    """TRAINS Multinomial Naive Bayes. [ACTION]"""
    return _train_and_evaluate(MultinomialNB(), data_url, target_column, 'classification')

# --- 7. Boosting ---
async def train_adaboost_classifier(data_url: str, target_column: str, n_estimators: int = 50) -> Dict[str, Any]:
    """TRAINS AdaBoost Classifier. [ACTION]"""
    return _train_and_evaluate(AdaBoostClassifier(n_estimators=n_estimators), data_url, target_column, 'classification')

async def train_gradient_boosting_classifier(data_url: str, target_column: str, n_estimators: int = 100) -> Dict[str, Any]:
    """TRAINS Gradient Boosting Classifier. [ACTION]"""
    return _train_and_evaluate(GradientBoostingClassifier(n_estimators=n_estimators), data_url, target_column, 'classification')
