
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
#   "xgboost",
# ]
# ///

from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.xgboost_server.tools import (
    sklearn_ops, native_ops, booster_ops, analysis_ops, super_ops
)
import structlog
from typing import List, Dict, Any, Optional, Union

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging(force_stderr=True)

mcp = FastMCP("xgboost_server", dependencies=["xgboost", "scikit-learn", "numpy", "pandas", "joblib", "scipy"])
DataInput = Union[List[List[Any]], List[Dict[str, Any]], str, Dict[str, Any]]
VectorInput = Union[List[Any], str]

# ==========================================
# 1. Sklearn Wrappers
# ==========================================
@mcp.tool()
async def xgb_classifier(X: DataInput, y: VectorInput, n_estimators: int = 100, learning_rate: float = 0.3, max_depth: int = 6, objective: str = 'binary:logistic', sample_weight: Optional[VectorInput] = None) -> Dict[str, Any]: 
    """TRAINS XGBoost Classifier. [ACTION]
    
    [RAG Context]
    A state-of-the-art Gradient Boosting "Super Tool" for classification tasks. XGBoost (Extreme Gradient Boosting) is renowned for its speed and performance on structured data.
    
    How to Use:
    - 'n_estimators': Number of boosting rounds (trees). 
    - 'learning_rate': Step size shrinkage used in update to prevents overfitting. 
    - 'max_depth': Maximum depth of a tree. Increasing this value will make the model more complex and more likely to overfit.
    
    Keywords: gradient boosting, gbm, ensemble classifier, tree boosting, extreme gradient.
    """
    return await sklearn_ops.xgb_classifier(X, y, n_estimators, learning_rate, max_depth, objective, sample_weight)
@mcp.tool()
async def xgb_regressor(X: DataInput, y: VectorInput, n_estimators: int = 100, learning_rate: float = 0.3, max_depth: int = 6, objective: str = 'reg:squarederror', sample_weight: Optional[VectorInput] = None) -> Dict[str, Any]: 
    """TRAINS XGBoost Regressor. [ACTION]
    
    [RAG Context]
    A high-performance "Super Tool" for numerical prediction. It uses an ensemble of gradient-boosted trees to capture complex non-linear relationships in data.
    
    How to Use:
    - Default 'objective' is 'reg:squarederror' for standard regression.
    - Highly resilient to missing data and automatically handles feature interactions.
    
    Keywords: gbm regression, boosted trees, forecast engine, numeric prediction.
    """
    return await sklearn_ops.xgb_regressor(X, y, n_estimators, learning_rate, max_depth, objective, sample_weight)
@mcp.tool()
async def xgb_ranker(X: DataInput, y: VectorInput, group: VectorInput, n_estimators: int = 100, learning_rate: float = 0.1, objective: str = 'rank:pairwise') -> Dict[str, Any]: 
    """TRAINS XGBoost Ranker. [ACTION]
    
    [RAG Context]
    A specialized Learning-to-Rank "Super Tool". It optimizes the relative order of items within groups (e.g., search results, recommendation lists), making it essential for ranking problems where exact values matter less than the sequence.
    
    How to Use:
    - 'group': An array containing the size of each query group.
    - 'objective': Typically 'rank:pairwise' or 'rank:ndcg'.
    - Ideal for building search engines, recommendation systems, or any list-sorting application.
    
    Keywords: learning to rank, ndcg, pairwise ranking, listwise optimization.
    """
    return await sklearn_ops.xgb_ranker(X, y, group, n_estimators, learning_rate, objective)
@mcp.tool()
async def xgb_rf_classifier(X: DataInput, y: VectorInput, n_estimators: int = 100, max_depth: int = 6) -> Dict[str, Any]: 
    """TRAINS XGBoost Random Forest. [ACTION]
    
    [RAG Context]
    A hybrid "Super Tool" that combines Random Forest subsampling with XGBoost's efficiency. It builds multiple trees in parallel rather than sequentially, offering a more robust alternative to standard GBM in some scenarios.
    
    How to Use:
    - Use this when standard XGBoost is overfitting or when you want the variance-reduction benefits of Random Forest logic with XGBoost's speed.
    
    Keywords: random forest boosting, parallel trees, ensemble model, forest classifier.
    """
    return await sklearn_ops.xgb_rf_classifier(X, y, n_estimators, max_depth)
@mcp.tool()
async def xgb_rf_regressor(X: DataInput, y: VectorInput, n_estimators: int = 100, max_depth: int = 6) -> Dict[str, Any]: 
    """TRAINS XGBoost RF Regressor. [ACTION]
    
    [RAG Context]
    A parallel-tree regressor that leverages the XGBoost engine to implement Random Forest algorithms. It is optimized for prediction stability on noisy datasets.
    
    How to Use:
    - Best suited for targets with high variance where bagging (bootstrap aggregating) provides better generalization than pure boosting.
    
    Keywords: rf regression, parallel boosting, stable prediction, ensemble regressor.
    """
    return await sklearn_ops.xgb_rf_regressor(X, y, n_estimators, max_depth)

# ==========================================
# 2. Native API
# ==========================================
@mcp.tool()
async def train_booster(X: DataInput, y: VectorInput, params: Dict[str, Any] = None, num_boost_round: int = 10, weight: Optional[VectorInput] = None) -> Dict[str, Any]: 
    """TRAINS native Booster. [ACTION]
    
    [RAG Context]
    The low-level "Super Tool" for advanced XGBoost users. It interacts directly with the XGBoost DMatrix and core training loop, offering maximum flexibility over hyperparameters and training callbacks.
    
    How to Use:
    - 'params': A dictionary of core parameters (e.g., {'eta': 0.1, 'silent': 1}).
    - 'num_boost_round': The number of boosting iterations.
    - Enables features not always available in the scikit-learn wrapper, like custom loss functions.
    
    Keywords: native xgboost, dmatrix training, core booster, custom gbm.
    """
    return await native_ops.train_booster(X, y, params, num_boost_round, weight)
@mcp.tool()
async def cv_booster(X: DataInput, y: VectorInput, params: Dict[str, Any] = None, num_boost_round: int = 10, nfold: int = 3, stratified: bool = False, metrics: List[str] = ['rmse'], seed: int = 0) -> Dict[str, Any]: 
    """RUNS Cross-Validation. [ACTION]
    
    [RAG Context]
    A diagnostic "Super Tool" for estimating model performance. It partitions the data into 'nfold' segments and performs repeated training/testing rounds to provide a robust estimate of generalization error.
    
    How to Use:
    - 'metrics': Choose evaluation metrics like 'auc', 'rmse', or 'mlogloss'.
    - Use this to fine-tune 'num_boost_round' and other parameters before final training to avoid overfitting to the training set.
    
    Keywords: cross validation, model evaluation, metric estimation, stratified sampling.
    """
    return await native_ops.cv_booster(X, y, params, num_boost_round, nfold, stratified, metrics, seed)

# ==========================================
# 3. Booster Operations
# ==========================================
@mcp.tool()
async def booster_predict(model: str, X: DataInput) -> List[float]: 
    """PREDICTS with Booster. [ACTION]
    
    [RAG Context]
    The execution "Super Tool" for XGBoost models. It takes a trained booster model (in JSON/binary format) and new input features to generate numerical predictions or probability scores.
    
    How to Use:
    - 'model': The serialized model string from 'booster_save' or 'train_booster'.
    - Use this for production inference after a model has been successfully tuned and validated.
    
    Keywords: inference engine, model scoring, forward pass, prediction values.
    """
    return await booster_ops.booster_predict(model, X)
@mcp.tool()
async def booster_save(model: str, format: str = 'json') -> str: 
    """SAVES Booster model. [ACTION]
    
    [RAG Context]
    A persistence "Super Tool". It converts an in-memory XGBoost booster into a serialized format (JSON or UBJSON) for storage or later retrieval.
    
    How to Use:
    - Default 'format' is 'json' for human-readable inspection.
    - Essential for checkpointing long-running training jobs or transferring models between different services/environments.
    
    Keywords: model serialization, model export, persistence, weight saving.
    """
    return await booster_ops.booster_save(model, format)
@mcp.tool()
async def booster_attributes(model: str) -> Dict[str, Any]: 
    """FETCHES model attributes. [DATA]
    
    [RAG Context]
    A metadata-retrieval "Super Tool". It extracts internal attributes and parameters from a saved XGBoost model, such as the best iteration number and user-defined metadata.
    
    How to Use:
    - Use this to audit a pre-trained model's history or to verify that the correct hyperparameter set was used during training.
    
    Keywords: model metadata, parameter check, audit log, internal state.
    """
    return await booster_ops.booster_attributes(model)

# ==========================================
# 4. Analysis
# ==========================================
@mcp.tool()
async def get_feature_importance(model: str, importance_type: str = 'weight') -> Dict[str, float]: 
    """GETS feature importance. [DATA]
    
    [RAG Context]
    An analytical "Super Tool" for model interpretability. It ranks the input features based on their contribution to the XGBoost model's decision-making process.
    
    How to Use:
    - 'importance_type': 'weight' (times a feature is used), 'gain' (relative contribution), or 'cover' (relative number of observations).
    - Use this to identify the "drivers" behind your model's predictions and perform feature selection.
    
    Keywords: feature ranking, model interpretability, variable importance, saliency map.
    """
    return await analysis_ops.get_feature_importance(model, importance_type)
@mcp.tool()
async def get_trees(model: str) -> List[str]: 
    """EXTRACTS tree structures. [DATA]
    
    [RAG Context]
    A deep-inspection "Super Tool" that dumps the raw structure of the boosted trees in the model. It allows technically proficient users (or agents) to audit the decision paths.
    
    How to Use:
    - Returns a list of strings where each string is a text representation of an individual decision tree.
    - Useful for verifying data-splitting logic and ensuring no "leaky" features are being prioritized.
    
    Keywords: tree dump, model audit, splitting logic, decision nodes.
    """
    return await analysis_ops.get_trees(model)

# ==========================================
# 5. Super Tools
# ==========================================
@mcp.tool()
async def auto_xgboost_clf(X: DataInput, y: VectorInput, n_iter: int = 10, cv: int = 3, scoring: str = 'accuracy') -> Dict[str, Any]: 
    """RUNS AutoML XGBoost. [ACTION]
    
    [RAG Context]
    A powerful "Super Tool" that performs an automated Hyperparameter Search (RandomizedSearchCV) for the best XGBoost configuration on your specific dataset.
    
    How to Use:
    - 'n_iter': Number of parameter settings that are sampled.
    - 'cv': Number of cross-validation folds.
    - Automates the tedious process of manual tuning to find the optimal model architecture.
    
    Keywords: automatic tuning, parameter search, hypopt, model optimization.
    """
    return await super_ops.auto_xgboost_clf(X, y, n_iter, cv, scoring)
@mcp.tool()
async def auto_xgboost_reg(X: DataInput, y: VectorInput, n_iter: int = 10, cv: int = 3, scoring: str = 'neg_mean_squared_error') -> Dict[str, Any]: 
    """RUNS AutoML Regressor. [ACTION]
    
    [RAG Context]
    An automated optimization "Super Tool" for regression. It searches for the best combination of XGBoost hyperparameters for numerical prediction tasks, minimizing manual trial-and-error.
    
    How to Use:
    - 'scoring': Typically 'neg_mean_squared_error' or 'neg_mean_absolute_error'.
    - Returns the best model found along with its performance metrics.
    
    Keywords: automatic regression, model search, hyperopt, auto ml.
    """
    return await super_ops.auto_xgboost_reg(X, y, n_iter, cv, scoring)

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class XgboostServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []

