
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
from mcp_servers.ml_server.tools import (
    automl, importance, clustering, anomaly, forecast
)
import structlog
from typing import Optional, Dict, List, Any, Union

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging import setup_logging
setup_logging()

mcp = FastMCP("ml_server", dependencies=["scikit-learn", "numpy", "pandas"])

@mcp.tool()
async def auto_ml(data_url: str, target_column: str, task_type: str = "auto", test_size: float = 0.2) -> str:
    """TRAINS AutoML model. [ACTION]
    
    [RAG Context]
    Automatically select and train the best ML model.
    Returns model metrics and path.
    """
    return await automl.auto_ml(data_url, target_column, task_type, test_size)

@mcp.tool()
async def feature_importance(data_url: str, target_column: str, method: str = "tree") -> str:
    """ANALYZES feature importance. [ACTION]
    
    [RAG Context]
    Analyze feature importance for prediction.
    Returns importance scores.
    """
    return await importance.feature_importance(data_url, target_column, method)

@mcp.tool()
async def convert_clustering(data_url: Optional[str] = None, data: Optional[Union[Dict, List]] = None, n_clusters: Any = 3, method: str = "kmeans") -> str:
    """CLUSTERS data. [ACTION]
    
    [RAG Context]
    Perform unsupervised clustering (KMeans, DBSCAN, etc).
    Returns cluster labels.
    """
    return await clustering.clustering(data_url, data, n_clusters, method)

@mcp.tool()
async def anomaly_detection(data_url: Optional[str] = None, data: Optional[Union[Dict, List]] = None, method: str = "isolation_forest", contamination: float = 0.1) -> str:
    """DETECTS anomalies. [ACTION]
    
    [RAG Context]
    Detect anomalies/outliers in data.
    Returns outlier indices.
    """
    return await anomaly.anomaly_detection(data_url, data, method, contamination)

@mcp.tool()
async def time_series_forecast(data_url: str, value_column: str, date_column: Optional[str] = None, periods: int = 10) -> str:
    """FORECASTS time series. [ACTION]
    
    [RAG Context]
    Forecast time series data.
    Returns forecast values.
    """
    return await forecast.time_series_forecast(data_url, value_column, date_column, periods)

if __name__ == "__main__":
    mcp.run()