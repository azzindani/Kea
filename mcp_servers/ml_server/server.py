
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

from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from tools import (
    automl, importance, clustering, anomaly, forecast
)
import structlog
from typing import Optional, Dict, List, Any, Union

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("ml_server", dependencies=["scikit-learn", "numpy", "pandas"])

@mcp.tool()
async def auto_ml(data_url: str, target_column: str, task_type: str = "auto", test_size: float = 0.2) -> str:
    """Automatically select and train the best ML model.
    Args:
        data_url: URL to CSV data
        target_column: Target variable to predict
        task_type: Task: classification or regression (default: auto)
        test_size: Test set proportion (0.1-0.4)
    """
    return await automl.auto_ml(data_url, target_column, task_type, test_size)

@mcp.tool()
async def feature_importance(data_url: str, target_column: str, method: str = "tree") -> str:
    """Analyze feature importance for prediction.
    Args:
        data_url: URL to CSV data
        target_column: Target variable
        method: Method: permutation, shap, tree (default: tree)
    """
    return await importance.feature_importance(data_url, target_column, method)

@mcp.tool()
async def convert_clustering(data_url: Optional[str] = None, data: Optional[Union[Dict, List]] = None, n_clusters: Any = 3, method: str = "kmeans") -> str:
    """Perform unsupervised clustering.
    Args:
        data_url: URL to CSV data
        data: Inline data: {columns: [], rows: []}
        n_clusters: Number of clusters (or 'auto')
        method: Method: kmeans, dbscan, hierarchical
    """
    return await clustering.clustering(data_url, data, n_clusters, method)

@mcp.tool()
async def anomaly_detection(data_url: Optional[str] = None, data: Optional[Union[Dict, List]] = None, method: str = "isolation_forest", contamination: float = 0.1) -> str:
    """Detect anomalies/outliers in data.
    Args:
        data_url: URL to CSV data
        data: Inline data: {columns: [], rows: []}
        method: Method: isolation_forest, lof, zscore
        contamination: Expected proportion of outliers
    """
    return await anomaly.anomaly_detection(data_url, data, method, contamination)

@mcp.tool()
async def time_series_forecast(data_url: str, value_column: str, date_column: Optional[str] = None, periods: int = 10) -> str:
    """Forecast time series data.
    Args:
        data_url: URL to CSV data
        value_column: Value column to forecast
        date_column: Date column name
        periods: Number of periods to forecast
    """
    return await forecast.time_series_forecast(data_url, value_column, date_column, periods)

if __name__ == "__main__":
    mcp.run()