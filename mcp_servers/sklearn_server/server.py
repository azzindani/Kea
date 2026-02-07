
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "joblib",
#   "mcp",
#   "numpy",
#   "pandas",
#   "scikit-learn",
#   "scipy",
#   "structlog",
#   "threadpoolctl",
# ]
# ///

from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from tools import (
    preprocess_ops, model_selection_ops, classification_ops, 
    regression_ops, clustering_ops, decomposition_ops, 
    ensemble_ops, super_ops, feature_selection_ops,
    manifold_ops, gaussian_process_ops, cross_decomposition_ops,
    semi_supervised_ops
)
import structlog
from typing import List, Dict, Any, Optional, Union

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("sklearn_server", dependencies=["scikit-learn", "numpy", "pandas", "joblib", "threadpoolctl", "scipy"])
DataInput = Union[List[List[Any]], List[Dict[str, Any]], str, Dict[str, Any]]
VectorInput = Union[List[Any], str]

# ==========================================
# 1. Preprocessing
# ==========================================
@mcp.tool()
async def fit_transform_scaler(data: DataInput, method: str = 'standard') -> Dict[str, Any]: 
    """SCALES data features. [ACTION]
    
    [RAG Context]
    Standardizes or normalizes features (StandardScaler, MinMaxScaler).
    Returns transformed data.
    """
    return await preprocess_ops.fit_transform_scaler(data, method)

@mcp.tool()
async def fit_transform_encoder(data: DataInput, method: str = 'label', columns: Optional[List[str]] = None) -> Dict[str, Any]: 
    """ENCODES categorical features. [ACTION]
    
    [RAG Context]
    Encodes categorical variables (LabelEncoder, OneHotEncoder).
    Returns transformed data.
    """
    return await preprocess_ops.fit_transform_encoder(data, method, columns)

@mcp.tool()
async def impute_missing(data: DataInput, strategy: str = 'mean', fill_value: Optional[Any] = None) -> Dict[str, Any]: 
    """IMPUTES missing values. [ACTION]
    
    [RAG Context]
    Fills missing data (SimpleImputer).
    Returns transformed data.
    """
    return await preprocess_ops.impute_missing(data, strategy, fill_value)

@mcp.tool()
async def generate_features(data: DataInput, method: str = 'poly', degree: int = 2) -> Dict[str, Any]: 
    """GENERATES new features. [ACTION]
    
    [RAG Context]
    Creates polynomial or interaction features.
    Returns transformed data.
    """
    return await preprocess_ops.generate_features(data, method, degree)

# ==========================================
# 2. Model Selection
# ==========================================
@mcp.tool()
async def split_data(X: DataInput, y: Optional[VectorInput] = None, test_size: float = 0.2, random_state: int = 42) -> Dict[str, Any]: 
    """SPLITS dataset. [ACTION]
    
    [RAG Context]
    Splits data into train and test sets.
    Returns dictionary with split data keys.
    """
    return await model_selection_ops.split_data(X, y, test_size, random_state)

@mcp.tool()
async def calculate_metrics(y_true: VectorInput, y_pred: VectorInput, task: str = 'classification') -> Dict[str, Any]: 
    """CALCULATES metrics. [ACTION]
    
    [RAG Context]
    Computes accuracy, precision, recall, f1, mse, r2, etc.
    Returns dictionary of metrics.
    """
    return await model_selection_ops.calculate_metrics(y_true, y_pred, task)

# ==========================================
# 3. Classification
# ==========================================
@mcp.tool()
async def logistic_regression(X: DataInput, y: VectorInput, C: float = 1.0, max_iter: int = 100) -> Dict[str, Any]: 
    """TRAINS Logistic Regression. [ACTION]
    
    [RAG Context]
    Linear classification model.
    Returns trained model metadata.
    """
    return await classification_ops.logistic_regression(X, y, C, max_iter)

@mcp.tool()
async def svc(X: DataInput, y: VectorInput, C: float = 1.0, kernel: str = 'rbf') -> Dict[str, Any]: 
    """TRAINS SVM Classifier. [ACTION]
    
    [RAG Context]
    Support Vector Classification (SVC).
    Returns trained model metadata.
    """
    return await classification_ops.svc(X, y, C, kernel)

@mcp.tool()
async def linear_svc(X: DataInput, y: VectorInput, C: float = 1.0) -> Dict[str, Any]: 
    """TRAINS Linear SVC. [ACTION]
    
    [RAG Context]
    Linear Support Vector Classification. Faster than SVC with linear kernel.
    Returns trained model metadata.
    """
    return await classification_ops.linear_svc(X, y, C)

@mcp.tool()
async def decision_tree_clf(X: DataInput, y: VectorInput, max_depth: Optional[int] = None) -> Dict[str, Any]: 
    """TRAINS Decision Tree Classifier. [ACTION]
    
    [RAG Context]
    Non-linear classification model.
    Returns trained model metadata.
    """
    return await classification_ops.decision_tree_clf(X, y, max_depth)

@mcp.tool()
async def knn_classifier(X: DataInput, y: VectorInput, n_neighbors: int = 5) -> Dict[str, Any]: 
    """TRAINS KNN Classifier. [ACTION]
    
    [RAG Context]
    K-Nearest Neighbors classification.
    Returns trained model metadata.
    """
    return await classification_ops.knn_classifier(X, y, n_neighbors)

@mcp.tool()
async def naive_bayes_gaussian(X: DataInput, y: VectorInput) -> Dict[str, Any]: 
    """TRAINS Gaussian Naive Bayes. [ACTION]
    
    [RAG Context]
    Probabilistic classification model.
    Returns trained model metadata.
    """
    return await classification_ops.naive_bayes_gaussian(X, y)

@mcp.tool()
async def mlp_classifier(X: DataInput, y: VectorInput, hidden_layer_sizes: List[int] = [100]) -> Dict[str, Any]: 
    """TRAINS MLP Classifier. [ACTION]
    
    [RAG Context]
    Multi-layer Perceptron (Neural Network) classification.
    Returns trained model metadata.
    """
    return await classification_ops.mlp_classifier(X, y, hidden_layer_sizes)

# ==========================================
# 4. Regression
# ==========================================
@mcp.tool()
async def linear_regression(X: DataInput, y: VectorInput) -> Dict[str, Any]: 
    """TRAINS Linear Regression. [ACTION]
    
    [RAG Context]
    Standard OLS linear regression.
    Returns trained model metadata.
    """
    return await regression_ops.linear_regression(X, y)

@mcp.tool()
async def ridge_regression(X: DataInput, y: VectorInput, alpha: float = 1.0) -> Dict[str, Any]: 
    """TRAINS Ridge Regression. [ACTION]
    
    [RAG Context]
    Linear regression with L2 regularization.
    Returns trained model metadata.
    """
    return await regression_ops.ridge_regression(X, y, alpha)

@mcp.tool()
async def lasso_regression(X: DataInput, y: VectorInput, alpha: float = 1.0) -> Dict[str, Any]: 
    """TRAINS Lasso Regression. [ACTION]
    
    [RAG Context]
    Linear regression with L1 regularization.
    Returns trained model metadata.
    """
    return await regression_ops.lasso_regression(X, y, alpha)

@mcp.tool()
async def elasticnet(X: DataInput, y: VectorInput, alpha: float = 1.0, l1_ratio: float = 0.5) -> Dict[str, Any]: 
    """TRAINS ElasticNet. [ACTION]
    
    [RAG Context]
    Linear regression with L1 and L2 regularization.
    Returns trained model metadata.
    """
    return await regression_ops.elasticnet(X, y, alpha, l1_ratio)

@mcp.tool()
async def svr(X: DataInput, y: VectorInput, C: float = 1.0, kernel: str = 'rbf') -> Dict[str, Any]: 
    """TRAINS SVM Regressor. [ACTION]
    
    [RAG Context]
    Support Vector Regression (SVR).
    Returns trained model metadata.
    """
    return await regression_ops.svr(X, y, C, kernel)

@mcp.tool()
async def decision_tree_reg(X: DataInput, y: VectorInput, max_depth: Optional[int] = None) -> Dict[str, Any]: 
    """TRAINS Decision Tree Regressor. [ACTION]
    
    [RAG Context]
    Non-linear regression model.
    Returns trained model metadata.
    """
    return await regression_ops.decision_tree_reg(X, y, max_depth)

@mcp.tool()
async def knn_regressor(X: DataInput, y: VectorInput, n_neighbors: int = 5) -> Dict[str, Any]: 
    """TRAINS KNN Regressor. [ACTION]
    
    [RAG Context]
    K-Nearest Neighbors regression.
    Returns trained model metadata.
    """
    return await regression_ops.knn_regressor(X, y, n_neighbors)

@mcp.tool()
async def mlp_regressor(X: DataInput, y: VectorInput, hidden_layer_sizes: List[int] = [100]) -> Dict[str, Any]: 
    """TRAINS MLP Regressor. [ACTION]
    
    [RAG Context]
    Multi-layer Perceptron (Neural Network) regression.
    Returns trained model metadata.
    """
    return await regression_ops.mlp_regressor(X, y, hidden_layer_sizes)

# ==========================================
# 5. Clustering
# ==========================================
@mcp.tool()
async def kmeans(X: DataInput, n_clusters: int = 8) -> Dict[str, Any]: 
    """TRAINS KMeans. [ACTION]
    
    [RAG Context]
    Centroid-based clustering.
    Returns trained model metadata.
    """
    return await clustering_ops.kmeans(X, n_clusters)

@mcp.tool()
async def dbscan(X: DataInput, eps: float = 0.5, min_samples: int = 5) -> Dict[str, Any]: 
    """TRAINS DBSCAN. [ACTION]
    
    [RAG Context]
    Density-based clustering.
    Returns trained model metadata.
    """
    return await clustering_ops.dbscan(X, eps, min_samples)

@mcp.tool()
async def agglomerative(X: DataInput, n_clusters: int = 2) -> Dict[str, Any]: 
    """TRAINS Agglomerative Clustering. [ACTION]
    
    [RAG Context]
    Hierarchical clustering.
    Returns trained model metadata.
    """
    return await clustering_ops.agglomerative(X, n_clusters)

@mcp.tool()
async def spectral_clustering(X: DataInput, n_clusters: int = 8) -> Dict[str, Any]: 
    """TRAINS Spectral Clustering. [ACTION]
    
    [RAG Context]
    Graph-based clustering.
    Returns trained model metadata.
    """
    return await clustering_ops.spectral_clustering(X, n_clusters)

# ==========================================
# 6. Decomposition
# ==========================================
@mcp.tool()
async def pca(X: DataInput, n_components: int = 2) -> Dict[str, Any]: 
    """PERFORMS PCA. [ACTION]
    
    [RAG Context]
    Principal Component Analysis (dimensionality reduction).
    Returns transformed data.
    """
    return await decomposition_ops.pca(X, n_components)

@mcp.tool()
async def tsne(X: DataInput, n_components: int = 2, perplexity: float = 30.0) -> Dict[str, Any]: 
    """PERFORMS t-SNE. [ACTION]
    
    [RAG Context]
    t-Distributed Stochastic Neighbor Embedding.
    Returns transformed data.
    """
    return await decomposition_ops.tsne(X, n_components, perplexity)

@mcp.tool()
async def nmf(X: DataInput, n_components: int = 2) -> Dict[str, Any]: 
    """PERFORMS NMF. [ACTION]
    
    [RAG Context]
    Non-Negative Matrix Factorization.
    Returns transformed data.
    """
    return await decomposition_ops.nmf(X, n_components)

@mcp.tool()
async def fast_ica(X: DataInput, n_components: int = 2) -> Dict[str, Any]: 
    """PERFORMS FastICA. [ACTION]
    
    [RAG Context]
    Independent Component Analysis.
    Returns transformed data.
    """
    return await decomposition_ops.fast_ica(X, n_components)

# ==========================================
# 7. Ensemble
# ==========================================
# ==========================================
# 7. Ensemble
# ==========================================
@mcp.tool()
async def random_forest_clf(X: DataInput, y: VectorInput, n_estimators: int = 100) -> Dict[str, Any]: 
    """TRAINS Random Forest Classifier. [ACTION]
    
    [RAG Context]
    Ensemble of Decision Trees (Bagging).
    Returns trained model metadata.
    """
    return await ensemble_ops.random_forest_clf(X, y, n_estimators)

@mcp.tool()
async def random_forest_reg(X: DataInput, y: VectorInput, n_estimators: int = 100) -> Dict[str, Any]: 
    """TRAINS Random Forest Regressor. [ACTION]
    
    [RAG Context]
    Ensemble of Decision Trees (Bagging).
    Returns trained model metadata.
    """
    return await ensemble_ops.random_forest_reg(X, y, n_estimators)

@mcp.tool()
async def gradient_boosting_clf(X: DataInput, y: VectorInput, n_estimators: int = 100, learning_rate: float = 0.1) -> Dict[str, Any]: 
    """TRAINS Gradient Boosting Classifier. [ACTION]
    
    [RAG Context]
    Ensemble of Decision Trees (Boosting).
    Returns trained model metadata.
    """
    return await ensemble_ops.gradient_boosting_clf(X, y, n_estimators, learning_rate)

@mcp.tool()
async def gradient_boosting_reg(X: DataInput, y: VectorInput, n_estimators: int = 100, learning_rate: float = 0.1) -> Dict[str, Any]: 
    """TRAINS Gradient Boosting Regressor. [ACTION]
    
    [RAG Context]
    Ensemble of Decision Trees (Boosting).
    Returns trained model metadata.
    """
    return await ensemble_ops.gradient_boosting_reg(X, y, n_estimators, learning_rate)

@mcp.tool()
async def adaboost_clf(X: DataInput, y: VectorInput, n_estimators: int = 50) -> Dict[str, Any]: 
    """TRAINS AdaBoost Classifier. [ACTION]
    
    [RAG Context]
    Adaptive Boosting ensemble.
    Returns trained model metadata.
    """
    return await ensemble_ops.adaboost_clf(X, y, n_estimators)

# ==========================================
# 8. Feature Selection
# ==========================================
@mcp.tool()
async def select_k_best(X: DataInput, y: VectorInput, k: int = 10, score_func: str = 'f_classif') -> Dict[str, Any]: 
    """SELECTS K best features. [ACTION]
    
    [RAG Context]
    Selects top K features based on univariate statistical tests.
    Returns transformed data.
    """
    return await feature_selection_ops.select_k_best(X, y, k, score_func)

@mcp.tool()
async def select_percentile(X: DataInput, y: VectorInput, percentile: int = 10, score_func: str = 'f_classif') -> Dict[str, Any]: 
    """SELECTS percentile features. [ACTION]
    
    [RAG Context]
    Selects top percentile of features.
    Returns transformed data.
    """
    return await feature_selection_ops.select_percentile(X, y, percentile, score_func)

@mcp.tool()
async def rfe(X: DataInput, y: VectorInput, n_features_to_select: int = 5, estimator_type: str = 'random_forest_clf') -> Dict[str, Any]: 
    """PERFORMS RFE. [ACTION]
    
    [RAG Context]
    Recursive Feature Elimination.
    Returns transformed data.
    """
    return await feature_selection_ops.rfe(X, y, n_features_to_select, estimator_type)

@mcp.tool()
async def variance_threshold(X: DataInput, threshold: float = 0.0) -> Dict[str, Any]: 
    """REMOVES low variance features. [ACTION]
    
    [RAG Context]
    Feature selection based on variance threshold.
    Returns transformed data.
    """
    return await feature_selection_ops.variance_threshold(X, threshold)

# ==========================================
# 9. Manifold Learning
# ==========================================
@mcp.tool()
async def isomap(X: DataInput, n_components: int = 2, n_neighbors: int = 5) -> Dict[str, Any]: 
    """PERFORMS Isomap. [ACTION]
    
    [RAG Context]
    Non-linear dimensionality reduction.
    Returns transformed data.
    """
    return await manifold_ops.isomap(X, n_components, n_neighbors)

@mcp.tool()
async def lle(X: DataInput, n_components: int = 2, n_neighbors: int = 5, method: str = 'standard') -> Dict[str, Any]: 
    """PERFORMS LLE. [ACTION]
    
    [RAG Context]
    Locally Linear Embedding.
    Returns transformed data.
    """
    return await manifold_ops.lle(X, n_components, n_neighbors, method)

@mcp.tool()
async def mds(X: DataInput, n_components: int = 2, metric: bool = True) -> Dict[str, Any]: 
    """PERFORMS MDS. [ACTION]
    
    [RAG Context]
    Multidimensional Scaling.
    Returns transformed data.
    """
    return await manifold_ops.mds(X, n_components, metric)

@mcp.tool()
async def spectral_embedding(X: DataInput, n_components: int = 2) -> Dict[str, Any]: 
    """PERFORMS Spectral Embedding. [ACTION]
    
    [RAG Context]
    Non-linear dimensionality reduction.
    Returns transformed data.
    """
    return await manifold_ops.spectral_embedding(X, n_components)

# ==========================================
# 10. Gaussian Processes
# ==========================================
# ==========================================
# 10. Gaussian Processes
# ==========================================
@mcp.tool()
async def gaussian_process_clf(X: DataInput, y: VectorInput) -> Dict[str, Any]: 
    """TRAINS Gaussian Process Classifier. [ACTION]
    
    [RAG Context]
    Probabilistic classification based on kernels.
    Returns trained model metadata.
    """
    return await gaussian_process_ops.gaussian_process_clf(X, y)

@mcp.tool()
async def gaussian_process_reg(X: DataInput, y: VectorInput) -> Dict[str, Any]: 
    """TRAINS Gaussian Process Regressor. [ACTION]
    
    [RAG Context]
    Probabilistic regression based on kernels.
    Returns trained model metadata.
    """
    return await gaussian_process_ops.gaussian_process_reg(X, y)

# ==========================================
# 11. Cross Decomposition
# ==========================================
@mcp.tool()
async def pls_regression(X: DataInput, Y: DataInput, n_components: int = 2) -> Dict[str, Any]: 
    """TRAINS PLS Regression. [ACTION]
    
    [RAG Context]
    Partial Least Squares regression.
    Returns trained model metadata.
    """
    return await cross_decomposition_ops.pls_regression(X, Y, n_components)

@mcp.tool()
async def cca(X: DataInput, Y: DataInput, n_components: int = 2) -> Dict[str, Any]: 
    """PERFORMS CCA. [ACTION]
    
    [RAG Context]
    Canonical Correlation Analysis.
    Returns transformed data.
    """
    return await cross_decomposition_ops.cca(X, Y, n_components)

# ==========================================
# 12. Semi-Supervised
# ==========================================
@mcp.tool()
async def label_propagation(X: DataInput, y: VectorInput, kernel: str = 'rbf') -> Dict[str, Any]: 
    """TRAINS Label Propagation. [ACTION]
    
    [RAG Context]
    Semi-supervised learning graph-based algorithm.
    Returns trained model metadata.
    """
    return await semi_supervised_ops.label_propagation(X, y, kernel)

@mcp.tool()
async def label_spreading(X: DataInput, y: VectorInput, kernel: str = 'rbf', alpha: float = 0.2) -> Dict[str, Any]: 
    """TRAINS Label Spreading. [ACTION]
    
    [RAG Context]
    Semi-supervised learning graph-based algorithm.
    Returns trained model metadata.
    """
    return await semi_supervised_ops.label_spreading(X, y, kernel, alpha)

@mcp.tool()
async def self_training(X: DataInput, y: VectorInput) -> Dict[str, Any]: 
    """TRAINS Self Training. [ACTION]
    
    [RAG Context]
    Semi-supervised learning with a base classifier.
    Returns trained model metadata.
    """
    return await semi_supervised_ops.self_training(X, y)

# ==========================================
# 13. Super Tools
# ==========================================
@mcp.tool()
async def automl_classifier(X: DataInput, y: VectorInput) -> Dict[str, Any]: 
    """RUNS AutoML Classifier. [ACTION]
    
    [RAG Context]
    Automatically selects and trains the best classification model.
    Returns trained model metadata.
    """
    return await super_ops.automl_classifier(X, y)

@mcp.tool()
async def pipeline_runner(X: DataInput, y: VectorInput, steps: List[str] = ['scaler', 'rf']) -> Dict[str, Any]: 
    """RUNS Pipeline. [ACTION]
    
    [RAG Context]
    Executes a sequence of data processing and modeling steps.
    Returns pipeline results.
    """
    return await super_ops.pipeline_runner(X, y, steps)


if __name__ == "__main__":
    mcp.run()