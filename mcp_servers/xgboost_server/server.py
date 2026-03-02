
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
async def xgb_ranker(X: DataInput, y: VectorInput, group: VectorInput, n_estimators: int = 100, learning_rate: float = 0.1, objective: str = 'rank:pairwise') -> Dict[str, Any]: return await sklearn_ops.xgb_ranker(X, y, group, n_estimators, learning_rate, objective)
@mcp.tool()
async def xgb_rf_classifier(X: DataInput, y: VectorInput, n_estimators: int = 100, max_depth: int = 6) -> Dict[str, Any]: return await sklearn_ops.xgb_rf_classifier(X, y, n_estimators, max_depth)
@mcp.tool()
async def xgb_rf_regressor(X: DataInput, y: VectorInput, n_estimators: int = 100, max_depth: int = 6) -> Dict[str, Any]: return await sklearn_ops.xgb_rf_regressor(X, y, n_estimators, max_depth)

# ==========================================
# 2. Native API
# ==========================================
@mcp.tool()
async def train_booster(X: DataInput, y: VectorInput, params: Dict[str, Any] = None, num_boost_round: int = 10, weight: Optional[VectorInput] = None) -> Dict[str, Any]: return await native_ops.train_booster(X, y, params, num_boost_round, weight)
@mcp.tool()
async def cv_booster(X: DataInput, y: VectorInput, params: Dict[str, Any] = None, num_boost_round: int = 10, nfold: int = 3, stratified: bool = False, metrics: List[str] = ['rmse'], seed: int = 0) -> Dict[str, Any]: return await native_ops.cv_booster(X, y, params, num_boost_round, nfold, stratified, metrics, seed)

# ==========================================
# 3. Booster Operations
# ==========================================
@mcp.tool()
async def booster_predict(model: str, X: DataInput) -> List[float]: return await booster_ops.booster_predict(model, X)
@mcp.tool()
async def booster_save(model: str, format: str = 'json') -> str: return await booster_ops.booster_save(model, format)
@mcp.tool()
async def booster_attributes(model: str) -> Dict[str, Any]: return await booster_ops.booster_attributes(model)

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
async def get_trees(model: str) -> List[str]: return await analysis_ops.get_trees(model)

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
async def auto_xgboost_reg(X: DataInput, y: VectorInput, n_iter: int = 10, cv: int = 3, scoring: str = 'neg_mean_squared_error') -> Dict[str, Any]: return await super_ops.auto_xgboost_reg(X, y, n_iter, cv, scoring)

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

