
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "mcp",
#   "numpy",
#   "pandas",
#   "scikit-learn",
#   "structlog",
# ]
# ///

from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
# from mcp_servers.ml_server.tools import (
#     automl, importance, clustering, anomaly, forecast
# )
# Note: Tools will be imported lazily inside each tool function to speed up startup.

import structlog
from typing import Optional, Dict, List, Any, Union

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging()


mcp = FastMCP("ml_server", dependencies=["scikit-learn", "numpy", "pandas", "xgboost"])

@mcp.tool()
async def auto_ml(data_url: str, target_column: str, task_type: str = "auto", test_size: float = 0.2) -> str:
    """TRAINS AutoML model. [ACTION]
    
    [RAG Context]
    Automatically select and train the best ML model.
    Returns model metrics and path.
    """
    from mcp_servers.ml_server.tools import automl
    return await automl.auto_ml(data_url, target_column, task_type, test_size)

@mcp.tool()
async def feature_importance(data_url: str, target_column: str, method: str = "tree") -> str:
    """ANALYZES feature importance. [ACTION]
    
    [RAG Context]
    Analyze feature importance for prediction.
    Returns importance scores.
    """
    from mcp_servers.ml_server.tools import importance
    return await importance.feature_importance(data_url, target_column, method)

@mcp.tool()
async def convert_clustering(data_url: Optional[str] = None, data: Optional[Union[Dict, List]] = None, n_clusters: Any = 3, method: str = "kmeans") -> str:
    """CLUSTERS data. [ACTION]
    
    [RAG Context]
    Perform unsupervised clustering (KMeans, DBSCAN, etc).
    Returns cluster labels.
    """
    from mcp_servers.ml_server.tools import clustering
    return await clustering.clustering(data_url, data, n_clusters, method)

@mcp.tool()
async def anomaly_detection(data_url: Optional[str] = None, data: Optional[Union[Dict, List]] = None, method: str = "isolation_forest", contamination: float = 0.1) -> str:
    """DETECTS anomalies. [ACTION]
    
    [RAG Context]
    Detect anomalies/outliers in data.
    Returns outlier indices.
    """
    from mcp_servers.ml_server.tools import anomaly
    return await anomaly.anomaly_detection(data_url, data, method, contamination)

@mcp.tool()
async def time_series_forecast(data_url: str, value_column: str, date_column: Optional[str] = None, periods: int = 10) -> str:
    """FORECASTS time series. [ACTION]
    
    [RAG Context]
    Forecast time series data.
    Returns forecast values.
    """
    from mcp_servers.ml_server.tools import forecast
    return await forecast.time_series_forecast(data_url, value_column, date_column, periods)


# ==========================================
# 6. XGBoost Operations (New)
# ==========================================
@mcp.tool()
async def train_xgboost_model(data_url: str, target_column: str, model_type: str = "classifier", params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """TRAINS XGBoost model. [ACTION]
    
    [RAG Context]
    Trains an XGBoost model (Classifier or Regressor) on the provided dataset.
    Returns model metrics and parameters.
    """
    from mcp_servers.ml_server.tools import xgboost_ops
    return await xgboost_ops.train_xgboost_model(data_url, target_column, model_type, params)

@mcp.tool()
async def cross_validate_xgboost(data_url: str, target_column: str, cv: int = 5, model_type: str = "classifier") -> Dict[str, Any]:
    """VALIDATES XGBoost model. [DATA]
    
    [RAG Context]
    Performs K-Fold Cross-Validation on XGBoost model.
    Returns mean score and std dev.
    """
    from mcp_servers.ml_server.tools import xgboost_ops
    return await xgboost_ops.cross_validate_xgboost(data_url, target_column, cv, model_type)

@mcp.tool()
async def analyze_xgboost_importance(data_url: str, target_column: str, importance_type: str = "gain") -> Dict[str, Any]:
    """ANALYZES feature importance. [DATA]
    
    [RAG Context]
    Extracts feature importance from a trained XGBoost model.
    """
    from mcp_servers.ml_server.tools import xgboost_ops
    return await xgboost_ops.analyze_xgboost_importance(data_url, target_column, importance_type)

# ==========================================
# 7. Hyperparameter Tuning (New)
# ==========================================
@mcp.tool()
async def perform_grid_search(data_url: str, target_column: str, model_name: str, param_grid: Dict[str, List[Any]], cv: int = 5, task: str = 'classifier') -> Dict[str, Any]:
    """TUNES hyperparameters via Grid. [ACTION]
    
    [RAG Context]
    Exhaustive search over specified parameter values.
    """
    from mcp_servers.ml_server.tools import tuning_ops
    return await tuning_ops.perform_grid_search(data_url, target_column, model_name, param_grid, cv, task)

@mcp.tool()
async def perform_random_search(data_url: str, target_column: str, model_name: str, param_distributions: Dict[str, List[Any]], n_iter: int = 10, cv: int = 5, task: str = 'classifier') -> Dict[str, Any]:
    """TUNES hyperparameters via Random. [ACTION]
    
    [RAG Context]
    Randomized search on hyper parameters.
    """
    from mcp_servers.ml_server.tools import tuning_ops
    return await tuning_ops.perform_random_search(data_url, target_column, model_name, param_distributions, n_iter, cv, task)


# ==========================================
# 8. Scikit-Learn Wrappers (New - Batch 1)
# ==========================================

# ==========================================
# 8. Scikit-Learn Wrappers (New - Batch 1)
# ==========================================
@mcp.tool()
async def train_knn_classifier(data_url: str, target_column: str, n_neighbors: int = 5) -> Dict[str, Any]:
    """TRAINS K-Nearest Neighbors Classifier. [ACTION]
    
    [RAG Context]
    Simple instance-based learning.
    """
    from mcp_servers.ml_server.tools import sklearn_wrappers
    return await sklearn_wrappers.train_knn_classifier(data_url, target_column, n_neighbors)

@mcp.tool()
async def train_knn_regressor(data_url: str, target_column: str, n_neighbors: int = 5) -> Dict[str, Any]:
    """TRAINS K-Nearest Neighbors Regressor. [ACTION]
    
    [RAG Context]
    Instance-based regression.
    """
    from mcp_servers.ml_server.tools import sklearn_wrappers
    return await sklearn_wrappers.train_knn_regressor(data_url, target_column, n_neighbors)

@mcp.tool()
async def train_svm_classifier(data_url: str, target_column: str, kernel: str = 'rbf', C: float = 1.0) -> Dict[str, Any]:
    """TRAINS Support Vector Machine Classifier. [ACTION]
    
    [RAG Context]
    Effective in high dimensional spaces.
    """
    from mcp_servers.ml_server.tools import sklearn_wrappers
    return await sklearn_wrappers.train_svm_classifier(data_url, target_column, kernel, C)

@mcp.tool()
async def train_svm_regressor(data_url: str, target_column: str, kernel: str = 'rbf', C: float = 1.0) -> Dict[str, Any]:
    """TRAINS Support Vector Machine Regressor. [ACTION]
    
    [RAG Context]
    SVR for regression.
    """
    from mcp_servers.ml_server.tools import sklearn_wrappers
    return await sklearn_wrappers.train_svm_regressor(data_url, target_column, kernel, C)

@mcp.tool()
async def train_decision_tree_classifier(data_url: str, target_column: str, max_depth: Optional[int] = None) -> Dict[str, Any]:
    """TRAINS Decision Tree Classifier. [ACTION]
    
    [RAG Context]
    Interpretable tree-based model.
    """
    from mcp_servers.ml_server.tools import sklearn_wrappers
    return await sklearn_wrappers.train_decision_tree_classifier(data_url, target_column, max_depth)

@mcp.tool()
async def train_decision_tree_regressor(data_url: str, target_column: str, max_depth: Optional[int] = None) -> Dict[str, Any]:
    """TRAINS Decision Tree Regressor. [ACTION]
    
    [RAG Context]
    Tree-based regression.
    """
    from mcp_servers.ml_server.tools import sklearn_wrappers
    return await sklearn_wrappers.train_decision_tree_regressor(data_url, target_column, max_depth)

@mcp.tool()
async def train_random_forest_classifier(data_url: str, target_column: str, n_estimators: int = 100, max_depth: Optional[int] = None) -> Dict[str, Any]:
    """TRAINS Random Forest Classifier. [ACTION]
    
    [RAG Context]
    Ensemble of decision trees.
    """
    from mcp_servers.ml_server.tools import sklearn_wrappers
    return await sklearn_wrappers.train_random_forest_classifier(data_url, target_column, n_estimators, max_depth)

@mcp.tool()
async def train_random_forest_regressor(data_url: str, target_column: str, n_estimators: int = 100, max_depth: Optional[int] = None) -> Dict[str, Any]:
    """TRAINS Random Forest Regressor. [ACTION]
    
    [RAG Context]
    Ensemble regression.
    """
    from mcp_servers.ml_server.tools import sklearn_wrappers
    return await sklearn_wrappers.train_random_forest_regressor(data_url, target_column, n_estimators, max_depth)

@mcp.tool()
async def train_logistic_regression(data_url: str, target_column: str, C: float = 1.0) -> Dict[str, Any]:
    """TRAINS Logistic Regression. [ACTION]
    
    [RAG Context]
    Linear classification.
    """
    from mcp_servers.ml_server.tools import sklearn_wrappers
    return await sklearn_wrappers.train_logistic_regression(data_url, target_column, C)

@mcp.tool()
async def train_linear_regression(data_url: str, target_column: str) -> Dict[str, Any]:
    """TRAINS Linear Regression. [ACTION]
    
    [RAG Context]
    OLS Regression.
    """
    from mcp_servers.ml_server.tools import sklearn_wrappers
    return await sklearn_wrappers.train_linear_regression(data_url, target_column)

@mcp.tool()
async def train_ridge_regression(data_url: str, target_column: str, alpha: float = 1.0) -> Dict[str, Any]:
    """TRAINS Ridge Regression. [ACTION]
    
    [RAG Context]
    L2 Regularized regression.
    """
    from mcp_servers.ml_server.tools import sklearn_wrappers
    return await sklearn_wrappers.train_ridge_regression(data_url, target_column, alpha)

@mcp.tool()
async def train_lasso_regression(data_url: str, target_column: str, alpha: float = 1.0) -> Dict[str, Any]:
    """TRAINS Lasso Regression. [ACTION]
    
    [RAG Context]
    L1 Regularized regression.
    """
    from mcp_servers.ml_server.tools import sklearn_wrappers
    return await sklearn_wrappers.train_lasso_regression(data_url, target_column, alpha)

@mcp.tool()
async def train_gaussian_nb(data_url: str, target_column: str) -> Dict[str, Any]:
    """TRAINS Gaussian Naive Bayes. [ACTION]
    
    [RAG Context]
    Probabilistic classifier.
    """
    from mcp_servers.ml_server.tools import sklearn_wrappers
    return await sklearn_wrappers.train_gaussian_nb(data_url, target_column)

@mcp.tool()
async def train_multinomial_nb(data_url: str, target_column: str) -> Dict[str, Any]:
    """TRAINS Multinomial Naive Bayes. [ACTION]
    
    [RAG Context]
    For text classification.
    """
    from mcp_servers.ml_server.tools import sklearn_wrappers
    return await sklearn_wrappers.train_multinomial_nb(data_url, target_column)

@mcp.tool()
async def train_adaboost_classifier(data_url: str, target_column: str, n_estimators: int = 50) -> Dict[str, Any]:
    """TRAINS AdaBoost Classifier. [ACTION]
    
    [RAG Context]
    Adaptive Boosting.
    """
    from mcp_servers.ml_server.tools import sklearn_wrappers
    return await sklearn_wrappers.train_adaboost_classifier(data_url, target_column, n_estimators)

@mcp.tool()
async def train_gradient_boosting_classifier(data_url: str, target_column: str, n_estimators: int = 100) -> Dict[str, Any]:
    """TRAINS Gradient Boosting Classifier. [ACTION]
    
    [RAG Context]
    Gradient boosted trees.
    """
    from mcp_servers.ml_server.tools import sklearn_wrappers
    return await sklearn_wrappers.train_gradient_boosting_classifier(data_url, target_column, n_estimators)


# ==========================================
# 9. Metrics (New - Batch 2)
# ==========================================

# ==========================================
# 9. Metrics (New - Batch 2)
# ==========================================
@mcp.tool()
def calculate_accuracy(y_true: List[int], y_pred: List[int]) -> float:
    """CALCULATES Accuracy Score. [DATA]
    
    [RAG Context]
    Fraction of correct predictions.
    """
    from mcp_servers.ml_server.tools import metrics_ops
    return metrics_ops.calculate_accuracy(y_true, y_pred)

@mcp.tool()
def calculate_precision(y_true: List[int], y_pred: List[int], average: str = 'binary') -> float:
    """CALCULATES Precision Score. [DATA]
    
    [RAG Context]
    TP / (TP + FP).
    """
    from mcp_servers.ml_server.tools import metrics_ops
    return metrics_ops.calculate_precision(y_true, y_pred, average)

@mcp.tool()
def calculate_recall(y_true: List[int], y_pred: List[int], average: str = 'binary') -> float:
    """CALCULATES Recall Score. [DATA]
    
    [RAG Context]
    TP / (TP + FN).
    """
    from mcp_servers.ml_server.tools import metrics_ops
    return metrics_ops.calculate_recall(y_true, y_pred, average)

@mcp.tool()
def calculate_f1(y_true: List[int], y_pred: List[int], average: str = 'binary') -> float:
    """CALCULATES F1 Score. [DATA]
    
    [RAG Context]
    Harmonic mean of precision and recall.
    """
    from mcp_servers.ml_server.tools import metrics_ops
    return metrics_ops.calculate_f1(y_true, y_pred, average)

@mcp.tool()
def calculate_roc_auc(y_true: List[int], y_score: List[float], multi_class: str = 'raise') -> float:
    """CALCULATES ROC AUC Score. [DATA]
    
    [RAG Context]
    Area Under Receiver Operating Characteristic Curve.
    """
    from mcp_servers.ml_server.tools import metrics_ops
    return metrics_ops.calculate_roc_auc(y_true, y_score, multi_class)

@mcp.tool()
def calculate_mse(y_true: List[float], y_pred: List[float]) -> float:
    """CALCULATES Mean Squared Error. [DATA]
    
    [RAG Context]
    Average squared difference.
    """
    from mcp_servers.ml_server.tools import metrics_ops
    return metrics_ops.calculate_mse(y_true, y_pred)

@mcp.tool()
def calculate_rmse(y_true: List[float], y_pred: List[float]) -> float:
    """CALCULATES Root Mean Squared Error. [DATA]
    
    [RAG Context]
    Square root of MSE.
    """
    from mcp_servers.ml_server.tools import metrics_ops
    return metrics_ops.calculate_rmse(y_true, y_pred)

@mcp.tool()
def calculate_mae(y_true: List[float], y_pred: List[float]) -> float:
    """CALCULATES Mean Absolute Error. [DATA]
    
    [RAG Context]
    Average absolute difference.
    """
    from mcp_servers.ml_server.tools import metrics_ops
    return metrics_ops.calculate_mae(y_true, y_pred)

@mcp.tool()
def calculate_r2(y_true: List[float], y_pred: List[float]) -> float:
    """CALCULATES R2 Score. [DATA]
    
    [RAG Context]
    Coefficient of determination.
    """
    from mcp_servers.ml_server.tools import metrics_ops
    return metrics_ops.calculate_r2(y_true, y_pred)


# ==========================================
# 10. Preprocessing (New - Batch 3)
# ==========================================
@mcp.tool()
def scale_standard(file_path: str, output_path: str) -> str:
    """SCALES data (StandardScaler). [ACTION]
    
    [RAG Context]
    Removes mean and scales to unit variance.
    """
    from mcp_servers.ml_server.tools import preprocessing_ops
    return preprocessing_ops.scale_standard(file_path, output_path)

@mcp.tool()
def scale_minmax(file_path: str, output_path: str) -> str:
    """SCALES data (MinMaxScaler). [ACTION]
    
    [RAG Context]
    Scales features to [0, 1] range.
    """
    from mcp_servers.ml_server.tools import preprocessing_ops
    return preprocessing_ops.scale_minmax(file_path, output_path)

@mcp.tool()
def scale_robust(file_path: str, output_path: str) -> str:
    """SCALES data (RobustScaler). [ACTION]
    
    [RAG Context]
    Scales using statistics that are robust to outliers.
    """
    from mcp_servers.ml_server.tools import preprocessing_ops
    return preprocessing_ops.scale_robust(file_path, output_path)

@mcp.tool()
def reduce_pca(file_path: str, n_components: int, output_path: str) -> str:
    """REDUCES dimensions (PCA). [ACTION]
    
    [RAG Context]
    Principal Component Analysis.
    """
    from mcp_servers.ml_server.tools import preprocessing_ops
    return preprocessing_ops.reduce_pca(file_path, n_components, output_path)

@mcp.tool()
def reduce_tsne(file_path: str, n_components: int, output_path: str, perplexity: float = 30.0) -> str:
    """REDUCES dimensions (t-SNE). [ACTION]
    
    [RAG Context]
    t-Distributed Stochastic Neighbor Embedding.
    """
    from mcp_servers.ml_server.tools import preprocessing_ops
    return preprocessing_ops.reduce_tsne(file_path, n_components, output_path, perplexity)


# ==========================================
# 11. Clustering (New)
# ==========================================
@mcp.tool()
def cluster_kmeans(data_url: str, n_clusters: int = 8) -> Dict[str, Any]:
    """CLUSTERS data using K-Means. [DATA]
    
    [RAG Context]
    Partitioning into K clusters.
    """
    from mcp_servers.ml_server.tools import clustering_ops
    return clustering_ops.cluster_kmeans(data_url, n_clusters)

@mcp.tool()
def cluster_dbscan(data_url: str, eps: float = 0.5) -> Dict[str, Any]:
    """CLUSTERS data using DBSCAN. [DATA]
    
    [RAG Context]
    Density-based clustering.
    """
    from mcp_servers.ml_server.tools import clustering_ops
    return clustering_ops.cluster_dbscan(data_url, eps)

@mcp.tool()
def cluster_spectral(data_url: str, n_clusters: int = 8) -> Dict[str, Any]:
    """CLUSTERS data using Spectral Clustering. [DATA]
    
    [RAG Context]
    Graph-based clustering.
    """
    from mcp_servers.ml_server.tools import clustering_ops
    return clustering_ops.cluster_spectral(data_url, n_clusters)

# ==========================================
# 12. Decomposition (New)
# ==========================================
@mcp.tool()
def decompose_pca(data_url: str, n_components: int = 2) -> Dict[str, Any]:
    """DECOMPOSES using PCA. [DATA]
    
    [RAG Context]
    Linear dimensionality reduction.
    """
    from mcp_servers.ml_server.tools import decomposition_ops
    return decomposition_ops.decompose_pca(data_url, n_components)

@mcp.tool()
def decompose_fast_ica(data_url: str, n_components: int = 2) -> Dict[str, Any]:
    """DECOMPOSES using FastICA. [DATA]
    
    [RAG Context]
    Independent Component Analysis.
    """
    from mcp_servers.ml_server.tools import decomposition_ops
    return decomposition_ops.decompose_fast_ica(data_url, n_components)

@mcp.tool()
def decompose_truncated_svd(data_url: str, n_components: int = 2) -> Dict[str, Any]:
    """DECOMPOSES using Truncated SVD. [DATA]
    
    [RAG Context]
    Latent Semantic Analysis.
    """
    from mcp_servers.ml_server.tools import decomposition_ops
    return decomposition_ops.decompose_truncated_svd(data_url, n_components)

# ==========================================
# 13. Ensemble & Selection (New)
# ==========================================
@mcp.tool()
def ensemble_bagging_classifier(data_url: str, target_col: str, n_estimators: int = 10) -> Dict[str, Any]:
    """TRAINS Bagging Classifier. [DATA]
    
    [RAG Context]
    Ensemble meta-estimator.
    """
    from mcp_servers.ml_server.tools import ensemble_ops
    return ensemble_ops.ensemble_bagging_classifier(data_url, target_col, n_estimators)

@mcp.tool()
def ensemble_isolation_forest(data_url: str, contamination: float = 0.1) -> Dict[str, Any]:
    """TRAINS Isolation Forest. [DATA]
    
    [RAG Context]
    Anomaly detection.
    """
    from mcp_servers.ml_server.tools import ensemble_ops
    return ensemble_ops.ensemble_isolation_forest(data_url, contamination)

@mcp.tool()
def select_k_best(data_url: str, target_col: str, k: int = 10) -> Dict[str, Any]:
    """SELECTS K Best Features. [DATA]
    
    [RAG Context]
    Feature selection via F-score.
    """
    from mcp_servers.ml_server.tools import ensemble_ops
    return ensemble_ops.select_k_best(data_url, target_col, k)


# ==========================================
# 11. Clustering (New)
# ==========================================
@mcp.tool()
def cluster_kmeans(data_url: str, n_clusters: int = 8) -> Dict[str, Any]:
    """CLUSTERS data using K-Means. [DATA]
    
    [RAG Context]
    Partitioning into K clusters.
    """
    from mcp_servers.ml_server.tools import clustering_ops
    return clustering_ops.cluster_kmeans(data_url, n_clusters)

@mcp.tool()
def cluster_dbscan(data_url: str, eps: float = 0.5) -> Dict[str, Any]:
    """CLUSTERS data using DBSCAN. [DATA]
    
    [RAG Context]
    Density-based clustering.
    """
    from mcp_servers.ml_server.tools import clustering_ops
    return clustering_ops.cluster_dbscan(data_url, eps)

@mcp.tool()
def cluster_spectral(data_url: str, n_clusters: int = 8) -> Dict[str, Any]:
    """CLUSTERS data using Spectral Clustering. [DATA]
    
    [RAG Context]
    Graph-based clustering.
    """
    from mcp_servers.ml_server.tools import clustering_ops
    return clustering_ops.cluster_spectral(data_url, n_clusters)

# ==========================================
# 12. Decomposition (New)
# ==========================================
@mcp.tool()
def decompose_pca(data_url: str, n_components: int = 2) -> Dict[str, Any]:
    """DECOMPOSES using PCA. [DATA]
    
    [RAG Context]
    Linear dimensionality reduction.
    """
    from mcp_servers.ml_server.tools import decomposition_ops
    return decomposition_ops.decompose_pca(data_url, n_components)

@mcp.tool()
def decompose_fast_ica(data_url: str, n_components: int = 2) -> Dict[str, Any]:
    """DECOMPOSES using FastICA. [DATA]
    
    [RAG Context]
    Independent Component Analysis.
    """
    from mcp_servers.ml_server.tools import decomposition_ops
    return decomposition_ops.decompose_fast_ica(data_url, n_components)

@mcp.tool()
def decompose_truncated_svd(data_url: str, n_components: int = 2) -> Dict[str, Any]:
    """DECOMPOSES using Truncated SVD. [DATA]
    
    [RAG Context]
    Latent Semantic Analysis.
    """
    from mcp_servers.ml_server.tools import decomposition_ops
    return decomposition_ops.decompose_truncated_svd(data_url, n_components)

# ==========================================
# 13. Ensemble & Selection (New)
# ==========================================
@mcp.tool()
def ensemble_bagging_classifier(data_url: str, target_col: str, n_estimators: int = 10) -> Dict[str, Any]:
    """TRAINS Bagging Classifier. [DATA]
    
    [RAG Context]
    Ensemble meta-estimator.
    """
    from mcp_servers.ml_server.tools import ensemble_ops
    return ensemble_ops.ensemble_bagging_classifier(data_url, target_col, n_estimators)

@mcp.tool()
def ensemble_isolation_forest(data_url: str, contamination: float = 0.1) -> Dict[str, Any]:
    """TRAINS Isolation Forest. [DATA]
    
    [RAG Context]
    Anomaly detection.
    """
    from mcp_servers.ml_server.tools import ensemble_ops
    return ensemble_ops.ensemble_isolation_forest(data_url, contamination)

@mcp.tool()
def select_k_best(data_url: str, target_col: str, k: int = 10) -> Dict[str, Any]:
    """SELECTS K Best Features. [DATA]
    
    [RAG Context]
    Feature selection via F-score.
    """
    from mcp_servers.ml_server.tools import ensemble_ops
    return ensemble_ops.select_k_best(data_url, target_col, k)

if __name__ == "__main__":


    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class MLServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []
