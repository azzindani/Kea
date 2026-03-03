
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

from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
# from mcp_servers.sklearn_server.tools import (
#     preprocess_ops, model_selection_ops, classification_ops, 
#     regression_ops, clustering_ops, decomposition_ops, 
#     ensemble_ops, super_ops, feature_selection_ops,
#     manifold_ops, gaussian_process_ops, cross_decomposition_ops,
#     semi_supervised_ops
# )
# Note: Tools will be imported lazily inside each tool function to speed up startup.

import structlog
from typing import List, Dict, Any, Optional, Union

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging(force_stderr=True)

import warnings
from sklearn.exceptions import ConvergenceWarning
warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

mcp = FastMCP("sklearn_server", dependencies=["scikit-learn", "numpy", "pandas", "joblib", "threadpoolctl", "scipy"])
DataInput = Union[List[List[Any]], List[Dict[str, Any]], str, Dict[str, Any]]
VectorInput = Union[List[Any], str]

# ==========================================
# 1. Preprocessing
# ==========================================
@mcp.tool()
async def fit_transform_scaler(data: DataInput, method: str = 'standard') -> Dict[str, Any]: 
    """SCALES and normalizes numerical features to a common range or distribution. [ACTION]
    
    [RAG Context]
    A mandatory "Preparation Super Tool" for almost all machine learning workflows. Many AI algorithms—particularly distance-based ones like KNN or gradient-based ones like SVM and Neural Networks—are highly sensitive to the absolute scale of numbers. If one feature is 'Income' (thousands) and another is 'Age' (tens), the model will mistakenly assume Income is 100x more important. This tool standardizes the data so that every feature participates on equal footing, drastically improving convergence speed and final accuracy. It is a core requirement for ensuring numerical stability and preventing specific features from "dominating" the learning process.
    
    How to Use:
    - 'standard': Sets Mean=0 and Variance=1. Mandatory for algorithms assuming a Gaussian distribution.
    - 'minmax': Compresses data into a fixed [0, 1] range. Best for image data or preserving zeros in sparse matrices.
    - 'robust': Uses Median and Interquartile Range. Recommended when your data contains significant "Outliers."
    
    Keywords: feature scaling, data normalization, z-score standardization, min-max scaling, data preprocessing, magnitude alignment.
    """
    from mcp_servers.sklearn_server.tools import preprocess_ops
    return await preprocess_ops.fit_transform_scaler(data, method)

@mcp.tool()
async def fit_transform_encoder(data: DataInput, method: str = 'label', columns: Optional[List[str]] = None) -> Dict[str, Any]: 
    """ENCODES categorical text labels into a numerical format readable by AI models. [ACTION]
    
    [RAG Context]
    A vital "translation tool" for bridging the gap between human language and machine learning. Computers cannot perform math on words like "Red," "Green," or "High." This tool converts such categorical variables into integers or binary vectors that a mathematical model can process. In the Kea corporate system, this is the primary method for handling categorical status codes, region names, and user categories. Choosing the right encoding method is critical to prevent the model from assuming a "false order" (e.g., thinking 'Category 2' is twice as large as 'Category 1').
    
    How to Use:
    - 'label': Assigns each unique string a unique integer (0, 1, 2...). Best for Target labels or Ordinal data (where order matters).
    - 'onehot': Creates a new binary [0, 1] column for every unique category. Best for "Nominal" data like colors or countries where there is no inherent ranking.
    - 'columns': Specify a subset of columns to encode, or let the tool auto-detect categorical types.
    
    Keywords: label encoding, one-hot encoding, feature vectorization, categorical transform, dummy variables, text-to-numeric.
    """
    from mcp_servers.sklearn_server.tools import preprocess_ops
    return await preprocess_ops.fit_transform_encoder(data, method, columns)

@mcp.tool()
async def impute_missing(data: DataInput, strategy: str = 'mean', fill_value: Optional[Any] = None) -> Dict[str, Any]: 
    """AUTOMATICALLY fills gaps and missing values in a dataset. [ACTION]
    
    [RAG Context]
    A critical "Data Healing Super Tool" for handling incomplete information. In real-world enterprise data, missing values are inevitable—sensors fail, users skip questions, and database joins result in 'NULLs'. Most machine learning models will crash if they encounter a single missing value. This tool rescues your dataset by "guessing" the missing values using advanced statistical strategies. It ensures that you don't have to delete valuable records just because they are missing a single piece of information, thereby preserving the "Statistical Power" of your entire dataset.
    
    How to Use:
    - 'mean' / 'median': Best for numerical data; fills gaps with the average/middle value.
    - 'most_frequent': Best for categorical data; fills gaps with the most common label.
    - 'constant': Fills gaps with a specific 'fill_value' provided by the user.
    - Extremely useful as part of a PRE-FLIGHT data cleaning pipeline before model training.
    
    Keywords: missing value imputation, data cleaning, gap filling, null replacement, dataset healing, statistical repair.
    """
    from mcp_servers.sklearn_server.tools import preprocess_ops
    return await preprocess_ops.impute_missing(data, strategy, fill_value)

@mcp.tool()
async def generate_features(data: DataInput, method: str = 'poly', degree: int = 2) -> Dict[str, Any]: 
    """CREATES sophisticated new features derived from existing data. [ACTION]
    
    [RAG Context]
    A high-level "Feature Engineering Super Tool" for capturing non-linear relationships. Sometimes the raw data (like 'Length' and 'Width') isn't enough for a linear model to understand a complex pattern (like 'Area'). This tool automatically generates "Interaction Features" (e.g., Length * Width) and "Polynomial Features" (e.g., Length squared). It effectively projects your data into a higher-dimensional space where simple models can learn complex, curved boundaries. This is the primary way the Kea system upgrades a basic "Linear Regression" into a powerful curve-fitting engine without needing deep learning.
    
    How to Use:
    - 'poly': Generates powers (x^2, x^3) and cross-products (x*y).
    - 'degree': Control the complexity. WARNING: setting degree > 3 on large datasets can cause "Feature Explosion" and slow down the system significantly.
    - Ideal for modeling physical systems, chemical reactions, or any growth trend that isn't a straight line.
    
    Keywords: polynomial features, interaction terms, feature engineering, high-dimensional expansion, non-linear transformation, feature synthesis.
    """
    from mcp_servers.sklearn_server.tools import preprocess_ops
    return await preprocess_ops.generate_features(data, method, degree)

# ==========================================
# 2. Model Selection
# ==========================================
@mcp.tool()
async def split_data(X: DataInput, y: Optional[VectorInput] = None, test_size: float = 0.2, random_state: int = 42) -> Dict[str, Any]: 
    """DIVIDES a dataset into two subsets: "Training" (to learn) and "Testing" (to evaluate). [ACTION]
    
    [RAG Context]
    A foundational "Scientific Protocol Tool" for validating AI performance. The most common mistake in machine learning is "Over-fitting"—where a model simply memorizes the training data but fails in the real world. By splitting your data, you hide a portion (the Test Set) from the model during training. This allows you to perform a "Blind Test" later to see how well the model actually generalizes to new, unseen information. This tool is a mandatory gatekeeper in the Kea system: no model can be finalized without first being validated on a clean, independent test split.
    
    How to Use:
    - 'test_size': Usually 0.2 (20%) or 0.3 (30%) is optimal.
    - 'random_state': Setting this ensures that every time you run the tool, you get the exact same split—critical for debugging and reproducible audits.
    - Always verify your model metrics on the "Test" portion to identify if your model is "Memorizing" instead of "Learning."
    
    Keywords: train-test split, model validation, holdout set, dataset division, shuffle split, scientific validation.
    """
    from mcp_servers.sklearn_server.tools import model_selection_ops
    return await model_selection_ops.split_data(X, y, test_size, random_state)

@mcp.tool()
async def calculate_metrics(y_true: VectorInput, y_pred: VectorInput, task: str = 'classification') -> Dict[str, Any]: 
    """CALCULATES a comprehensive suite of performance metrics for model evaluation. [ACTION]
    
    [RAG Context]
    The ultimate "Model Audit Super Tool." Training a model is only half the battle; knowing if it actually works is what separates professional AI from toys. This tool compares your model's "Predictions" against the "Actual Truth" to quantify exactly how much you can trust the system. For classification, it calculates Accuracy (overall correctness), Precision (avoiding false alarms), Recall (not missing any targets), and the F1-Score (the balanced harmonic mean). For regression, it measures the Average Error (MAE/MSE) and the R-Squared (the "Fit" quality). In a RAG context, this tool is the primary way the system decides which model version to deploy or whether a newly trained agent is ready for production.
    
    How to Use:
    - 'task': Set to 'classification' for discrete labels or 'regression' for numeric forecasts.
    - Always use this after the 'predict' phase of your workflow.
    - If Precision is high but Recall is low, your model is too "conservative"—it only predicts when it is 100% sure, missing many valid cases.
    
    Keywords: performance metrics, model evaluation, error audit, precision-recall, f1 analysis, model validation.
    """
    from mcp_servers.sklearn_server.tools import model_selection_ops
    return await model_selection_ops.calculate_metrics(y_true, y_pred, task)

# ==========================================
# 3. Classification
# ==========================================
@mcp.tool()
async def logistic_regression(X: DataInput, y: VectorInput, C: float = 1.0, max_iter: int = 100) -> Dict[str, Any]: 
    """TRAINS a Logistic Regression model for probabilistic classification. [ACTION]
    
    [RAG Context]
    A bedrock "Baseline Super Tool" for industrial-strength classification. Despite the word "regression," this is a classifier that models the probability of a data point belonging to a specific category (e.g., "Is this email Spam or Not?"). It is the most widely used model in finance and medicine because it is "Explainable"—you can see exactly which features (like 'Income' or 'Blood Pressure') increased the probability of a specific outcome. It is perfect for cases where you need more than just a "Yes/No" answer, but actual confidence scores to make business decisions.
    
    How to Use:
    - 'C': Inverse regularization strength. Smaller values (e.g., 0.01) prevent the model from "over-focusing" on specific columns.
    - Best for binary problems (2 classes) or multi-class problems where the boundary between classes is relatively linear.
    - Highly efficient and fast to train, making it the ideal first choice for any classification task.
    
    Keywords: logistic regression, binary classifier, probability estimator, explainable ai, baseline classification, logit model.
    """
    from mcp_servers.sklearn_server.tools import classification_ops
    return await classification_ops.logistic_regression(X, y, C, max_iter)

@mcp.tool()
async def svc(X: DataInput, y: VectorInput, C: float = 1.0, kernel: str = 'rbf') -> Dict[str, Any]: 
    """TRAINS a Support Vector Machine (SVM) for complex, non-linear classification. [ACTION]
    
    [RAG Context]
    A heavy-duty "High-Dimensional Super Tool" for finding optimal boundaries in messy data. SVM works by projecting your data into a higher-dimensional space and finding the "Maximum Margin Hyperplane"—essentially the widest possible "neutral zone" between two categories. It is incredibly powerful for small to medium datasets where the relationship between features is complex or "curvy." In the Kea system, this is the preferred tool for high-accuracy tasks like facial recognition, credit risk scoring, and text classification where simple linear models fail.
    
    How to Use:
    - 'kernel': 'rbf' (Radial Basis Function) is the default and can handle almost any non-linear shape. Use 'linear' for simpler, faster training.
    - 'C': The penalty for misclassification. Smaller C makes the boundary smoother (more general), larger C makes it more complex (fitting training data exactly).
    - NOTE: Requires feature scaling (using 'fit_transform_scaler') for optimal results.
    
    Keywords: support vector classifier, svc, kernel trick, hyperplane optimization, non-linear boundary, high-accuracy classification.
    """
    from mcp_servers.sklearn_server.tools import classification_ops
    return await classification_ops.svc(X, y, C, kernel)

@mcp.tool()
async def linear_svc(X: DataInput, y: VectorInput, C: float = 1.0) -> Dict[str, Any]: 
    """TRAINS a high-performance Linear Support Vector Classifier. [ACTION]
    
    [RAG Context]
    A specialized, "Speed-Optimized Super Tool" for large-scale linear classification. While the standard 'svc' can handle complex curves, 'linear_svc' is built specifically for datasets where we know (or suspect) the boundary is a straight line. It is significantly faster and consumes less memory than the rbf-kernel counterpart, making it the primary choice for "Text Classification" (NLP) and massive-scale binary filtering tasks. It implements a more efficient solver that can handle millions of rows where a standard SVM would stall.
    
    How to Use:
    - Best for cases with a high number of features (e.g., word counts in a document).
    - 'C': Regularization strength. Tweak this to find the balance between model simplicity and training accuracy.
    - Like standard SVM, this tool MUST be preceded by feature scaling to perform correctly.
    
    Keywords: linear svm, fast classifier, large-scale learning, nlp classifier, feature-rich learning, linear separation.
    """
    from mcp_servers.sklearn_server.tools import classification_ops
    return await classification_ops.linear_svc(X, y, C)

@mcp.tool()
async def decision_tree_clf(X: DataInput, y: VectorInput, max_depth: Optional[int] = None) -> Dict[str, Any]: 
    """TRAINS an Interpretable Decision Tree for rule-based classification. [ACTION]
    
    [RAG Context]
    A transparent "White-Box Super Tool" that makes decisions just like a human—by following a series of "If-Then" questions. Unlike "Black-Box" models (like Neural Networks), a Decision Tree can be easily visualized and explained to stakeholders (e.g., "The loan was denied because INCOME < 30k AND DEBT > 5k"). This makes it the primary tool for regulated industries where every automated decision must be justified. It is also uniquely "Robust"—it doesn't care about the scale of your data and can handle categorical labels and numerical features simultaneously.
    
    How to Use:
    - 'max_depth': The single most important parameter. If left None, the tree will grow until it perfectly memorizes the training data (Overfitting). Set a limit (e.g., 3 or 5) for better real-world performance.
    - Ideal for rapid prototyping and for discovering which features are actually driving the classification results.
    
    Keywords: decision tree, rule-based ai, cart model, interpretable classification, feature importance, transparent modeling.
    """
    from mcp_servers.sklearn_server.tools import classification_ops
    return await classification_ops.decision_tree_clf(X, y, max_depth)

@mcp.tool()
async def knn_classifier(X: DataInput, y: VectorInput, n_neighbors: int = 5) -> Dict[str, Any]: 
    """TRAINS a K-Neighbors Classifier based on local data similarity. [ACTION]
    
    [RAG Context]
    A simple yet elegant "Intuitive Super Tool" that classifies new points based on the "Company they Keep"—it simply looks for the 5 most similar records in the training set and adopts their majority label. It is a "Non-Parametric" model, meaning it doesn't make any assumptions about the underlying math; it just follows the data density. This is essential for recommendation systems (e.g., "Users like you also bought X") and for cases where the boundary between classes is extremely irregular and hard to model with a single math equation.
    
    How to Use:
    - 'n_neighbors': The number of "friends" to consult. A small number (1-3) makes the model very sensitive to local noise; a large number (10-20) makes it more stable and generalized.
    - MANDATORY: This tool calculated distances, so you MUST use 'fit_transform_scaler' first, or the features with larger numbers will drown out the others.
    
    Keywords: k-nearest neighbors, knn, similarity search, instance-based learning, proximity classifier, case-based reasoning.
    """
    from mcp_servers.sklearn_server.tools import classification_ops
    return await classification_ops.knn_classifier(X, y, n_neighbors)

@mcp.tool()
async def naive_bayes_gaussian(X: DataInput, y: VectorInput) -> Dict[str, Any]: 
    """TRAINS Gaussian Naive Bayes. [ACTION]
    
    [RAG Context]
    Probabilistic classification model.
    Returns trained model metadata.
    """
    from mcp_servers.sklearn_server.tools import classification_ops
    return await classification_ops.naive_bayes_gaussian(X, y)

@mcp.tool()
async def mlp_classifier(X: DataInput, y: VectorInput, hidden_layer_sizes: List[int] = [100]) -> Dict[str, Any]: 
    """TRAINS MLP Classifier. [ACTION]
    
    [RAG Context]
    Multi-layer Perceptron (Neural Network) classification.
    Returns trained model metadata.
    """
    from mcp_servers.sklearn_server.tools import classification_ops
    return await classification_ops.mlp_classifier(X, y, hidden_layer_sizes)

# ==========================================
# 4. Regression
# ==========================================
@mcp.tool()
async def linear_regression(X: DataInput, y: VectorInput) -> Dict[str, Any]: 
    """TRAINS a classic Ordinary Least Squares (OLS) Linear Regression model. [ACTION]
    
    [RAG Context]
    The absolute "Gold Standard Super Tool" for statistical modeling and predictive analytics. Linear Regression seeks to find the "Line of Best Fit" that minimizes the squared distance between your predictions and the actual data points. It is the most widely understood model in science and business, used for everything from predicting sales growth to estimating the impact of marketing spend. Its primary advantage is "Simplicity"—you receive clear mathematical weights that tell you exactly how much each input feature contributes to the final outcome.
    
    How to Use:
    - Ideal for datasets where features have a proportional, straight-line relationship with the target.
    - Extremely fast to train, making it perfect for rapid data discovery.
    - WARNING: Sensitive to massive outliers, which can "pull" the line away from the main data cluster.
    
    Keywords: linear regression, ols, best fit line, predictive modeling, trend analysis, statistical fitting.
    """
    from mcp_servers.sklearn_server.tools import regression_ops
    return await regression_ops.linear_regression(X, y)

@mcp.tool()
async def ridge_regression(X: DataInput, y: VectorInput, alpha: float = 1.0) -> Dict[str, Any]: 
    """TRAINS a Ridge Regression model with L2 regularization for stability. [ACTION]
    
    [RAG Context]
    An elite "Robust Regression Super Tool" designed to handle datasets where features are highly correlated (Multi-collinearity). Traditional regression can "explode" (produce massive, unstable coefficients) when features overlap too much. Ridge Regression solves this by adding a "Penalty" (L2 regularization) to the size of the coefficients, forcing them to be smaller and more stable. This is a mandatory requirement for datasets with many features that might be redundant, ensuring the model remains reliable in the face of minor data variations.
    
    How to Use:
    - 'alpha': Controls the "strength" of the penalty. Larger alpha makes the model more robust/simpler; smaller alpha makes it behave more like classic OLS.
    - Mandatory for "High-Dimensional" datasets where the number of features is close to the number of records.
    
    Keywords: ridge regression, l2 regularization, tikhonov regularization, robust fitting, coefficient shrinking, stable regression.
    """
    from mcp_servers.sklearn_server.tools import regression_ops
    return await regression_ops.ridge_regression(X, y, alpha)

@mcp.tool()
async def lasso_regression(X: DataInput, y: VectorInput, alpha: float = 1.0) -> Dict[str, Any]: 
    """TRAINS a Lasso Regression model with L1 regularization for "Automatic Feature Selection." [ACTION]
    
    [RAG Context]
    A clever "Filtering Super Tool" that simultaneously models your data and identifies which features are useless. Lasso (L1 regularization) has a unique mathematical property: it doesn't just "shrink" coefficients; it forces the coefficients of less-important features to exactly ZERO. This effectively performs "Automatic Feature Selection," leaving you with a sparse, efficient model that only uses the most impactful signals. It is the primary tool for high-dimensional "Needle in a Haystack" problems where you have 100 features but only 10 actually matter for the prediction.
    
    How to Use:
    - 'alpha': Regularization strength. Tweak this to control how "aggressive" the feature filtering becomes.
    - Results in a much "Cleaner" model that is easier to explain and cheaper to run in production.
    - PRE-FLIGHT: Requires feature scaling for the L1 penalty to apply fairly across all columns.
    
    Keywords: lasso regression, l1 regularization, feature selection, sparse modeling, coefficient zeroing, automated filtering.
    """
    from mcp_servers.sklearn_server.tools import regression_ops
    return await regression_ops.lasso_regression(X, y, alpha)

@mcp.tool()
async def elasticnet(X: DataInput, y: VectorInput, alpha: float = 1.0, l1_ratio: float = 0.5) -> Dict[str, Any]: 
    """TRAINS an ElasticNet model combining L1 and L2 regularization for maximum flexibility. [ACTION]
    
    [RAG Context]
    A sophisticated "Best-of-Both-Worlds Super Tool" for complex regression problems. ElasticNet combines the feature-selection power of Lasso (L1) with the stability of Ridge (L2). This is especially critical when you have "Groups" of correlated features—Lasso might arbitrarily pick just one, while ElasticNet will tend to include the whole group while keeping them stable. In the Kea corporate system, this is the default recommendation for training linear models on high-dimensional tabular data when you aren't sure whether you need filtering or stabilizing more.
    
    How to Use:
    - 'l1_ratio': Set to 1.0 for pure Lasso, 0.0 for pure Ridge. The default 0.5 provides a balanced hybrid approach.
    - 'alpha': Overall strength of the penalty. 
    - Essential for sophisticated genomic data, financial cross-impact modeling, and large-scale sensor analysis.
    
    Keywords: elasticnet, hybrid regularization, l1 l2 penalty, robust regression, feature grouping, optimized estimator.
    """
    from mcp_servers.sklearn_server.tools import regression_ops
    return await regression_ops.elasticnet(X, y, alpha, l1_ratio)

@mcp.tool()
async def svr(X: DataInput, y: VectorInput, C: float = 1.0, kernel: str = 'rbf') -> Dict[str, Any]: 
    """TRAINS a Support Vector Regressor (SVR) for robust, non-linear numerical prediction. [ACTION]
    
    [RAG Context]
    A heavy-duty "Non-Linear Super Tool" that brings the power of SVM to numerical forecasting. Unlike classic regression which tries to hit every point, SVR tries to fit the data within a "Tolerance Tube" (Epsilon). It is uniquely resilient to "Individual Outliers"—as long as a data point is within the tube, it doesn't pull the model away. This makes it the primary choice for "High-Precision" forecasting in engineering and physics where you want a model that learns the "General Trend" without being distracted by minor sensor noise or temporary spikes.
    
    How to Use:
    - 'kernel': Use 'rbf' for complex, curvy trends; 'linear' for straight trends.
    - 'C': The cost of being outside the tolerance tube. High C fits exactly; low C creates a more flexible, generalized model.
    - PRE-FLIGHT: You MUST perform 'fit_transform_scaler' first, as SVR is a distance-based algorithm.
    
    Keywords: support vector regression, svr, non-linear forecast, robust regression, epsilon-insensitive, kernel regression.
    """
    from mcp_servers.sklearn_server.tools import regression_ops
    return await regression_ops.svr(X, y, C, kernel)

@mcp.tool()
async def decision_tree_reg(X: DataInput, y: VectorInput, max_depth: Optional[int] = None) -> Dict[str, Any]: 
    """TRAINS Decision Tree Regressor. [ACTION]
    
    [RAG Context]
    Non-linear regression model.
    Returns trained model metadata.
    """
    from mcp_servers.sklearn_server.tools import regression_ops
    return await regression_ops.decision_tree_reg(X, y, max_depth)

@mcp.tool()
async def knn_regressor(X: DataInput, y: VectorInput, n_neighbors: int = 5) -> Dict[str, Any]: 
    """TRAINS KNN Regressor. [ACTION]
    
    [RAG Context]
    K-Nearest Neighbors regression.
    Returns trained model metadata.
    """
    from mcp_servers.sklearn_server.tools import regression_ops
    return await regression_ops.knn_regressor(X, y, n_neighbors)

@mcp.tool()
async def mlp_regressor(X: DataInput, y: VectorInput, hidden_layer_sizes: List[int] = [100]) -> Dict[str, Any]: 
    """TRAINS a Multi-layer Perceptron (Neural Network) for complex numerical forecasting. [ACTION]
    
    [RAG Context]
    A powerful "Deep Learning Super Tool" in the Scikit-learn family. The MLP Regressor is a bridge between traditional statistics and modern AI; it uses layers of artificial "Neurons" to learn intricate, non-linear relationships that simple regression models would miss. This is the primary engine for high-stakes forecasting—like predicting stock prices, electricity demand, or complex chemical yields—where thousands of variables interact in a "Secret" way. It is capable of approximating any continuous mathematical function given enough data.
    
    How to Use:
    - 'hidden_layer_sizes': Defines the architecture. `[100, 50]` creates two layers—one with 100 neurons and one with 50.
    - PRE-FLIGHT: Neural networks are extremely sensitive to scale. You MUST perform 'fit_transform_scaler' before training.
    - It is a "Black Box" model; it provides top-tier accuracy but is difficult to explain to humans.
    
    Keywords: neural network regression, mlp, deep learning regressor, non-linear forecasting, artificial intelligence, weight optimization.
    """
    from mcp_servers.sklearn_server.tools import regression_ops
    return await regression_ops.mlp_regressor(X, y, hidden_layer_sizes)

# ==========================================
# 5. Clustering
# ==========================================
@mcp.tool()
async def kmeans(X: DataInput, n_clusters: int = 8) -> Dict[str, Any]: 
    """TRAINS a KMeans clustering model to discover natural groups in your data. [ACTION]
    
    [RAG Context]
    The most popular "Unsupervised Learning Super Tool" for segmentation and pattern discovery. KMeans automatically organizes your dataset into 'N' distinct groups (Clusters) by finding the mathematical center (Centroid) of each group. It is the primary engine for "Customer Segmentation" (grouping users with similar buying habits), "Image Compression" (grouping similar colors), and "Anomaly Detection" (identifying points that are far from any cluster). It allows the system to make sense of massive, unlabeled datasets by revealing the hidden "Geographic Locations" of data categories.
    
    How to Use:
    - 'n_clusters': The number of groups you expect to find. If you aren't sure, try the "Elbow Method"—run the tool multiple times with different N and look for the point where the error stops dropping significantly.
    - MANDATORY: You MUST perform 'fit_transform_scaler' before running KMeans, as it is strictly distance-based.
    - Resulting cluster labels allow you to treat members of the same group with the same business logic.
    
    Keywords: kmeans clustering, unsupervised learning, customer segmentation, centroid discovery, data grouping, pattern recognition.
    """
    from mcp_servers.sklearn_server.tools import clustering_ops
    return await clustering_ops.kmeans(X, n_clusters)

@mcp.tool()
async def dbscan(X: DataInput, eps: float = 0.5, min_samples: int = 5) -> Dict[str, Any]: 
    """TRAINS a DBSCAN model for density-based clustering and outlier detection. [ACTION]
    
    [RAG Context]
    A sophisticated "Topology-Aware Super Tool" that finds clusters of arbitrary shapes. Unlike KMeans (which only finds circles/blobs), DBSCAN (Density-Based Spatial Clustering of Applications with Noise) looks for "Streets" or "Chains" of high data density. Most importantly, it is the premier tool for "Automatic Outlier Detection"—it doesn't force every point into a cluster; if a point is in a "lonely" part of the data space, it is labeled as Noise (-1). This makes it essential for fraud detection, geographic spatial analysis, and identifying rare anomalies in high-traffic telemetry.
    
    How to Use:
    - 'eps': The maximum distance between two samples for one to be considered as in the neighborhood of the other. Smaller eps results in more, smaller clusters.
    - 'min_samples': The number of neighbors required to form a "Core Point."
    - No need to pre-specify the number of clusters; the algorithm will discover them automatically.
    
    Keywords: dbscan, density-based clustering, noise detection, outlier labeling, spatial analysis, automatic clustering.
    """
    from mcp_servers.sklearn_server.tools import clustering_ops
    return await clustering_ops.dbscan(X, eps, min_samples)

@mcp.tool()
async def agglomerative(X: DataInput, n_clusters: int = 2) -> Dict[str, Any]: 
    """TRAINS Agglomerative Clustering. [ACTION]
    
    [RAG Context]
    Hierarchical clustering.
    Returns trained model metadata.
    """
    from mcp_servers.sklearn_server.tools import clustering_ops
    return await clustering_ops.agglomerative(X, n_clusters)

@mcp.tool()
async def spectral_clustering(X: DataInput, n_clusters: int = 8) -> Dict[str, Any]: 
    """TRAINS Spectral Clustering. [ACTION]
    
    [RAG Context]
    Graph-based clustering.
    Returns trained model metadata.
    """
    from mcp_servers.sklearn_server.tools import clustering_ops
    return await clustering_ops.spectral_clustering(X, n_clusters)

# ==========================================
# 6. Decomposition
# ==========================================
@mcp.tool()
async def pca(X: DataInput, n_components: int = 2) -> Dict[str, Any]: 
    """PERFORMS Principal Component Analysis (PCA) for dimensionality reduction. [ACTION]
    
    [RAG Context]
    The absolute "Information Extraction Super Tool" for data compression and visualization. High-dimensional data (e.g., 50 different metrics) is impossible for humans to visualize and often redundant for machines. PCA finds the "Principal Components"—the specific directions where the data varies the most—and projects the dataset onto these new axes. It allows the system to take a 100-column spreadsheet and compress it into just 2 or 3 columns that capture 90% of the original "Signal." This is a mandatory step for high-speed clustering, removing noise from signals, and creating 2D/3D plots of complex datasets.
    
    How to Use:
    - 'n_components': The target number of dimensions (e.g., set to 2 for a standard flat plot).
    - MANDATORY: Data MUST be centered and scaled via 'fit_transform_scaler' before PCA to ensure that all features are treated fairly by their variance.
    - Use this to identify which "factors" are actually driving the differences in your data.
    
    Keywords: dimensionality reduction, feature compression, variance maximization, eigenvector projection, noise reduction, data visualization.
    """
    from mcp_servers.sklearn_server.tools import decomposition_ops
    return await decomposition_ops.pca(X, n_components)

@mcp.tool()
async def tsne(X: DataInput, n_components: int = 2, perplexity: float = 30.0) -> Dict[str, Any]: 
    """PERFORMS t-Distributed Stochastic Neighbor Embedding (t-SNE) for non-linear manifold mapping. [ACTION]
    
    [RAG Context]
    An elite "High-Dimensional Visualization Super Tool." While PCA looks for global variance, t-SNE focuses on keeping "Neighbors" together. It is an iterative, non-linear algorithm that is famous for revealing "Hidden Clusters" in extremely complex data, such as gene expression or high-level image embeddings. It "unfolds" complex manifolds so that they can be viewed in 2D or 3D. It is the primary way the Kea system creates "Maps" of abstract concepts, where similar items are grouped together in a way that is visually intuitive for human operators.
    
    How to Use:
    - 'perplexity': Controls the balance between local and global aspects of the data. Higher values consider more neighbors.
    - WARNING: t-SNE is computationally expensive; for massive datasets with hundreds of features, run PCA first to reduce to ~50 dimensions before calling t-SNE.
    - Results are for visualization/representation only and cannot be directly used to "map" new data points without re-running the entire fit.
    
    Keywords: t-sne, non-linear mapping, neighbor embedding, cluster visualization, manifold learning, high-dimensional map.
    """
    from mcp_servers.sklearn_server.tools import decomposition_ops
    return await decomposition_ops.tsne(X, n_components, perplexity)

@mcp.tool()
async def nmf(X: DataInput, n_components: int = 2) -> Dict[str, Any]: 
    """PERFORMS NMF. [ACTION]
    
    [RAG Context]
    Non-Negative Matrix Factorization.
    Returns transformed data.
    """
    from mcp_servers.sklearn_server.tools import decomposition_ops
    return await decomposition_ops.nmf(X, n_components)

@mcp.tool()
async def fast_ica(X: DataInput, n_components: int = 2) -> Dict[str, Any]: 
    """PERFORMS Independent Component Analysis (ICA) to separate mixed signals. [ACTION]
    
    [RAG Context]
    A specialized "Signal Separation Super Tool" famous for the "Cocktail Party Problem." While PCA looks for correlated variance, ICA looks for statistical Independence. If you have two microphones in a room with two people talking, each mic hears a "Mix" of both voices. ICA can mathematically "un-mix" them into the two original independent voices. This is essential for removing artifacts from EEG/brain signals, separating different instruments in a song, and identifying independent economic drivers that are overlapping in raw market data.
    
    How to Use:
    - 'n_components': The number of independent sources you are trying to recover.
    - Best for cases where you suspect the underlying "causes" of your data are additive and independent.
    - Essential for high-purity signal processing and feature extraction where noise and signal are intertwined.
    
    Keywords: independent component analysis, ica, signal separation, source recovery, blind source separation, data un-mixing.
    """
    from mcp_servers.sklearn_server.tools import decomposition_ops
    return await decomposition_ops.fast_ica(X, n_components)

# ==========================================
# 7. Ensemble
# ==========================================
# ==========================================
# 7. Ensemble
# ==========================================
@mcp.tool()
async def random_forest_clf(X: DataInput, y: VectorInput, n_estimators: int = 100) -> Dict[str, Any]: 
    """TRAINS a Random Forest Classifier using an ensemble of decision trees. [ACTION]
    
    [RAG Context]
    A world-class "Ensemble Super Tool" that is often the first choice for complex classification problems. Random Forest works by creating a "Forest" of many independent decision trees, each trained on a random subset of the data. During prediction, it takes a "Vote" among all trees to decide the final category. This "Wisdom of the Crowd" approach makes it incredibly stable, accurate, and resistant to "Over-fitting"—if one tree gets distracted by noise, the other 99 trees will out-vote it. It is the primary workhorse for enterprise-grade fraud detection, churn prediction, and risk assessment.
    
    How to Use:
    - 'n_estimators': The number of trees in the forest. Generally, more trees provide a more stable model but take longer to train. 100 is a great starting point.
    - Does NOT require feature scaling (scaler), making it one of the easiest and most reliable tools to use out of the box.
    - Provides a "Feature Importance" report, showing exactly which data columns were most useful for making decisions.
    
    Keywords: random forest, ensemble classification, forest model, bagged trees, robust classifier, majority vote.
    """
    from mcp_servers.sklearn_server.tools import ensemble_ops
    return await ensemble_ops.random_forest_clf(X, y, n_estimators)

@mcp.tool()
async def random_forest_reg(X: DataInput, y: VectorInput, n_estimators: int = 100) -> Dict[str, Any]: 
    """TRAINS a Random Forest Regressor for high-precision numerical forecasting. [ACTION]
    
    [RAG Context]
    A premier "Ensemble Forecasting Super Tool" that brings extraordinary stability to numerical predictions. By averaging the outputs of multiple randomized decision trees, the Random Forest Regressor effectively "smooths out" the errors that might plague a single model. It is exceptionally good at handling non-linear relationships and interactions between features without needing complex math setups. In the Kea system, this is the "Go-To" tool for predicting inventory demand, pricing strategies, and sensor-based physical properties where the underlying patterns are complex and multi-faceted.
    
    How to Use:
    - Highly resilient to missing data and outliers; it can handle noisy real-world enterprise data with ease.
    - 'n_estimators': Set to 100 or 200 for best balance of speed and accuracy.
    - Like the classifier, it provides a "Feature Importance" score, helping you understand which variables are truly driving your numerical outcomes.
    
    Keywords: random forest regression, bagged trees ensemble, numerical forecasting, robust regressor, forest forecast, ensemble modeling.
    """
    from mcp_servers.sklearn_server.tools import ensemble_ops
    return await ensemble_ops.random_forest_reg(X, y, n_estimators)

@mcp.tool()
async def gradient_boosting_clf(X: DataInput, y: VectorInput, n_estimators: int = 100, learning_rate: float = 0.1) -> Dict[str, Any]: 
    """TRAINS a Gradient Boosting Classifier for state-of-the-art predictive accuracy. [ACTION]
    
    [RAG Context]
    A top-tier "Iterative Improvement Super Tool" and a frequent winner of data science competitions. Unlike Random Forest (where trees are independent), Gradient Boosting builds trees one-by-one, where each new tree specifically tries to "Correct the Mistakes" of the previous ones. This results in a model that is incredibly precise and capable of capturing subtle patterns that other models miss. It is the gold standard for high-stakes tasks like identifying rare fraud, diagnosing diseases, and predicting customer conversion in competitive markets.
    
    How to Use:
    - 'learning_rate': Controls how quickly the model tries to correct itself. A smaller rate (e.g., 0.05) combined with more 'n_estimators' often leads to a much better model, though it takes longer to train.
    - More sensitive to "Over-fitting" than Random Forest—it is critical to use 'split_data' and 'calculate_metrics' to monitor its performance on unseen data.
    
    Keywords: gradient boosting, gbm, iterative ensemble, boosted trees, high-precision classification, sequential learning.
    """
    from mcp_servers.sklearn_server.tools import ensemble_ops
    return await ensemble_ops.gradient_boosting_clf(X, y, n_estimators, learning_rate)

@mcp.tool()
async def gradient_boosting_reg(X: DataInput, y: VectorInput, n_estimators: int = 100, learning_rate: float = 0.1) -> Dict[str, Any]: 
    """TRAINS Gradient Boosting Regressor. [ACTION]
    
    [RAG Context]
    Ensemble of Decision Trees (Boosting).
    Returns trained model metadata.
    """
    from mcp_servers.sklearn_server.tools import ensemble_ops
    return await ensemble_ops.gradient_boosting_reg(X, y, n_estimators, learning_rate)

@mcp.tool()
async def adaboost_clf(X: DataInput, y: VectorInput, n_estimators: int = 50) -> Dict[str, Any]: 
    """TRAINS AdaBoost Classifier. [ACTION]
    
    [RAG Context]
    Adaptive Boosting ensemble.
    Returns trained model metadata.
    """
    from mcp_servers.sklearn_server.tools import ensemble_ops
    return await ensemble_ops.adaboost_clf(X, y, n_estimators)

# ==========================================
# 8. Feature Selection
# ==========================================
@mcp.tool()
async def select_k_best(X: DataInput, y: VectorInput, k: int = 10, score_func: str = 'f_classif') -> Dict[str, Any]: 
    """SELECTS the top 'K' most statistically significant features for your model. [ACTION]
    
    [RAG Context]
    A high-speed "Univariate Feature Selection Super Tool" for simplifying complex models. Often, a dataset contains 100 columns, but only 10 are actually relevant to the target—the others are just "Noise" that distracts the model. This tool uses rigorous statistical tests (like ANOVA or Chi-Squared) to rank every feature and discard the ones that have no mathematical relationship with the outcome. This results in models that are faster to train, cheaper to run, and much easier for human operators to understand and audit.
    
    How to Use:
    - 'k': The number of features you want to keep.
    - 'score_func': 'f_classif' for classification tasks; 'f_regression' for numerical tasks.
    - Use this EARLY in your pipeline (right after scaling) to remove garbage data and "Dimensionality Bloat" before starting heavy model training.
    
    Keywords: feature selection, univariate filter, k-best features, dimensionality reduction, statistical ranking, feature pruning.
    """
    from mcp_servers.sklearn_server.tools import feature_selection_ops
    return await feature_selection_ops.select_k_best(X, y, k, score_func)

@mcp.tool()
async def select_percentile(X: DataInput, y: VectorInput, percentile: int = 10, score_func: str = 'f_classif') -> Dict[str, Any]: 
    """SELECTS percentile features. [ACTION]
    
    [RAG Context]
    Selects top percentile of features.
    Returns transformed data.
    """
    from mcp_servers.sklearn_server.tools import feature_selection_ops
    return await feature_selection_ops.select_percentile(X, y, percentile, score_func)

@mcp.tool()
async def rfe(X: DataInput, y: VectorInput, n_features_to_select: int = 5, estimator_type: str = 'random_forest_clf') -> Dict[str, Any]: 
    """PERFORMS Recursive Feature Elimination (RFE) to find the absolute "Power Features." [ACTION]
    
    [RAG Context]
    A premium "Model-Based Feature Selection Super Tool." Unlike simple statistical tests, RFE works by training a real model, identifying which features it used THE LEAST, and then deleting them. It does this over and over (recursively) until only the specified number of "Power Features" remain. This is the ultimate way to find features that only matter when they interact with each other—patterns that 'select_k_best' would miss. It ensures your model is as efficient as possible by keeping only the "High-Octane" ingredients in the data mix.
    
    How to Use:
    - 'estimator_type': The model used to "judge" the features. 'random_forest_clf' is usually the most reliable judge.
    - 'n_features_to_select': The size of the final "elite" feature set.
    - WARNING: Computationally expensive, as it trains multiple models. Best used for "finalizing" a high-stakes model after initial discovery.
    
    Keywords: rfe, recursive feature elimination, model-based selection, elite feature set, interactive feature discovery, feature pruning.
    """
    from mcp_servers.sklearn_server.tools import feature_selection_ops
    return await feature_selection_ops.rfe(X, y, n_features_to_select, estimator_type)

@mcp.tool()
async def variance_threshold(X: DataInput, threshold: float = 0.0) -> Dict[str, Any]: 
    """REMOVES low variance features. [ACTION]
    
    [RAG Context]
    Feature selection based on variance threshold.
    Returns transformed data.
    """
    from mcp_servers.sklearn_server.tools import feature_selection_ops
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
    from mcp_servers.sklearn_server.tools import manifold_ops
    return await manifold_ops.isomap(X, n_components, n_neighbors)

@mcp.tool()
async def lle(X: DataInput, n_components: int = 2, n_neighbors: int = 5, method: str = 'standard') -> Dict[str, Any]: 
    """PERFORMS LLE. [ACTION]
    
    [RAG Context]
    Locally Linear Embedding.
    Returns transformed data.
    """
    from mcp_servers.sklearn_server.tools import manifold_ops
    return await manifold_ops.lle(X, n_components, n_neighbors, method)

@mcp.tool()
async def mds(X: DataInput, n_components: int = 2, metric: bool = True) -> Dict[str, Any]: 
    """PERFORMS MDS. [ACTION]
    
    [RAG Context]
    Multidimensional Scaling.
    Returns transformed data.
    """
    from mcp_servers.sklearn_server.tools import manifold_ops
    return await manifold_ops.mds(X, n_components, metric)

@mcp.tool()
async def spectral_embedding(X: DataInput, n_components: int = 2) -> Dict[str, Any]: 
    """PERFORMS Spectral Embedding. [ACTION]
    
    [RAG Context]
    Non-linear dimensionality reduction.
    Returns transformed data.
    """
    from mcp_servers.sklearn_server.tools import manifold_ops
    return await manifold_ops.spectral_embedding(X, n_components)

# ==========================================
# 10. Gaussian Processes
# ==========================================
# ==========================================
# 10. Gaussian Processes
# ==========================================
@mcp.tool()
async def gaussian_process_clf(X: DataInput, y: VectorInput) -> Dict[str, Any]: 
    """TRAINS a Gaussian Process Classifier (GPC) for probabilistic, uncertainty-aware classification. [ACTION]
    
    [RAG Context]
    An elite "Bayesian Super Tool" that doesn't just give a classification, but also tells you how "Uncertain" it is about its prediction. Unlike standard models, GPC uses a "Kernel" to model the relationship between points as a multi-dimensional probability distribution. This is essential for high-stakes business decisions where being "Wrong" is expensive (e.g., medical diagnosis or satellite control). It allows the system to say: "I think this is Category A, but I only have 60% confidence—maybe a human should check this."
    
    How to Use:
    - Excellent for small datasets where capturing accurate uncertainty is more important than raw speed.
    - Computationally heavy: not recommended for datasets with more than a few thousand rows.
    - Provides a "Variance" or "Confidence Interval" that can be used to trigger fallback manual review DAGs.
    
    Keywords: gaussian process, gpc, bayesian classification, uncertainty estimation, kernel-based learning, probabilistic modeling.
    """
    from mcp_servers.sklearn_server.tools import gaussian_process_ops
    return await gaussian_process_ops.gaussian_process_clf(X, y)

@mcp.tool()
async def gaussian_process_reg(X: DataInput, y: VectorInput) -> Dict[str, Any]: 
    """TRAINS Gaussian Process Regressor. [ACTION]
    
    [RAG Context]
    Probabilistic regression based on kernels.
    Returns trained model metadata.
    """
    from mcp_servers.sklearn_server.tools import gaussian_process_ops
    return await gaussian_process_ops.gaussian_process_reg(X, y)

# ==========================================
# 11. Cross Decomposition
# ==========================================
@mcp.tool()
async def pls_regression(X: DataInput, Y: DataInput, n_components: int = 2) -> Dict[str, Any]: 
    """TRAINS a Partial Least Squares (PLS) Regression for modeling multiple correlated outcomes. [ACTION]
    
    [RAG Context]
    A specialized "Chemometric Super Tool" designed for datasets where you have many features AND multiple targets that all interact. PLS Regression works like a hybrid between PCA and OLS; it finds the directions in the input space that best explain the variance in the output space. This is the primary algorithm for NIR spectroscopy, industrial manufacturing, and economic modeling where a single input (like Temperature) might affect five different outputs (like Yield, Purity, and Speed) simultaneously.
    
    How to Use:
    - 'n_components': The number of latent variables to extract. 
    - Ideal for cases where the number of features is much larger than the number of samples (the "Small N, Large P" problem).
    - Prevents over-fitting by compressing the input data into the most relevant "Actionable" components for the specific target.
    
    Keywords: pls regression, partial least squares, multi-target modeling, latent variable regression, chemometrics, industrial prediction.
    """
    from mcp_servers.sklearn_server.tools import cross_decomposition_ops
    return await cross_decomposition_ops.pls_regression(X, Y, n_components)

@mcp.tool()
async def cca(X: DataInput, Y: DataInput, n_components: int = 2) -> Dict[str, Any]: 
    """PERFORMS CCA. [ACTION]
    
    [RAG Context]
    Canonical Correlation Analysis.
    Returns transformed data.
    """
    from mcp_servers.sklearn_server.tools import cross_decomposition_ops
    return await cross_decomposition_ops.cca(X, Y, n_components)

# ==========================================
# 12. Semi-Supervised
# ==========================================
@mcp.tool()
async def label_propagation(X: DataInput, y: VectorInput, kernel: str = 'rbf') -> Dict[str, Any]: 
    """TRAINS a Label Propagation model for semi-supervised learning on partially labeled data. [ACTION]
    
    [RAG Context]
    A clever "Knowledge Transfer Super Tool" for cases where you have a lot of data but only a few labels. In real companies, labeling data is expensive (paying humans to tag images). Label Propagation works by treating the dataset as a "Social Network"—it starts with the few labeled points and "spreads" those labels to their most similar neighbors across the data graph. This allows the system to "Auto-Label" thousands of new records based on just a handful of manual examples, drastically reducing the cost and time required to build a functioning classifier.
    
    How to Use:
    - Pass a dataset 'y' where unknown items are marked with -1.
    - The algorithm will "flow" the known labels into the -1 items based on similarity.
    - Essential for rapid cold-start of new AI services where ground-truth data is scarce.
    
    Keywords: label propagation, semi-supervised learning, label spreading, pseudo-labeling, graph-based learning, active learning engine.
    """
    from mcp_servers.sklearn_server.tools import semi_supervised_ops
    return await semi_supervised_ops.label_propagation(X, y, kernel)

@mcp.tool()
async def label_spreading(X: DataInput, y: VectorInput, kernel: str = 'rbf', alpha: float = 0.2) -> Dict[str, Any]: 
    """TRAINS Label Spreading. [ACTION]
    
    [RAG Context]
    Semi-supervised learning graph-based algorithm.
    Returns trained model metadata.
    """
    from mcp_servers.sklearn_server.tools import semi_supervised_ops
    return await semi_supervised_ops.label_spreading(X, y, kernel, alpha)

@mcp.tool()
async def self_training(X: DataInput, y: VectorInput) -> Dict[str, Any]: 
    """TRAINS Self Training. [ACTION]
    
    [RAG Context]
    Semi-supervised learning with a base classifier.
    Returns trained model metadata.
    """
    from mcp_servers.sklearn_server.tools import semi_supervised_ops
    return await semi_supervised_ops.self_training(X, y)

# ==========================================
# 13. Super Tools
# ==========================================
@mcp.tool()
async def automl_classifier(X: DataInput, y: VectorInput) -> Dict[str, Any]: 
    """RUNS an Automated Machine Learning (AutoML) race to find the best model for your data. [ACTION]
    
    [RAG Context]
    The ultimate "Decision-Support Super Tool" for the Kea system. Instead of the user choosing a specific algorithm, 'automl_classifier' hosts a "Tournament"—it tries Logistic Regression, Random Forests, Gradient Boosting, and SVMs all at once. It uses cross-validation to independently judge which model captures the dataset's unique patterns with the least error. This "Auto-Pilot" mode is the primary way the corporate kernel scales its intelligence without needing a human data scientist to manually tune every single sub-process.
    
    How to Use:
    - Pass your raw features and labels for any classification task.
    - Returns the best-performing model along with a report on how the other contenders performed.
    - The perfect starting point for any new classification problem—let the computer find the best math for you.
    
    Keywords: automl, automated machine learning, model search, best model tournament, auto-clf, optimization engine.
    """
    from mcp_servers.sklearn_server.tools import super_ops
    return await super_ops.automl_classifier(X, y)

@mcp.tool()
async def pipeline_runner(X: DataInput, y: VectorInput, steps: List[str] = ['scaler', 'rf']) -> Dict[str, Any]: 
    """RUNS a standardized multi-stage machine learning pipeline in a single atomic block. [ACTION]
    
    [RAG Context]
    A grand-master "Orchestration Super Tool" for ensuring enterprise-grade structural integrity. In high-stakes AI, "Data Leakage" (accidentally letting the model see the test answers during training) is a fatal error. 'pipeline_runner' prevents this by bonding the Scaler, Imputer, and Model together into a single "Black Box" that is treated as one unit. This ensures that every transformation applied to the training data is exactly repeated for the test data and production data, ensuring 100% consistency and reliability in every prediction.
    
    How to Use:
    - 'steps': Provide an ordered list of codes, e.g., `['imputer', 'scaler', 'random_forest_clf']`.
    - It is the primary way to build "Production-Ready" predictive services in the Kea architecture.
    - Ensures that your entire data-to-prediction lifecycle is repeatable, auditable, and mathematically sound.
    
    Keywords: ml pipeline, data flow orchestration, atomic workflow, consistent training, end-to-end model, model pipe.
    """
    from mcp_servers.sklearn_server.tools import super_ops
    return await super_ops.pipeline_runner(X, y, steps)


if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class SklearnServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []

