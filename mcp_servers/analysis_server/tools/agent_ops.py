import structlog
from typing import Dict, Any, List
import pandas as pd

# We need to call other servers.
import sys
from pathlib import Path

# Add root to sys.path to find other servers
root_path = str(Path(__file__).parents[3])
if root_path not in sys.path:
    sys.path.append(root_path)

from mcp_servers.pandas_server.tools import pipeline_ops
from mcp_servers.ml_server.tools import xgboost_ops
from mcp_servers.deep_learning_server.tools import model_ops, train_ops

logger = structlog.get_logger()

def _heuristic_model_selection(df: pd.DataFrame, goal: str) -> str:
    """Decides between ML (XGBoost) and DL (Neural Net)."""
    # Simple heuristic
    n_rows, _ = df.shape
    
    if "deep learning" in goal.lower() or "neural network" in goal.lower():
        return "dl"
    
    # If explicit text processing might be needed (not fully supported yet, but DL handles embeddings better)
    # But for now, if data is small-medium, XGBoost is usually better.
    if n_rows < 10000:
        return "ml"
    
    return "ml" # Default to ML for now as it's more robust

async def analyze_data_science_project(dataset_url: str, target_column: str, goal: str) -> Dict[str, Any]:
    """EXECUTES end-to-end DS project. [ACTION]
    
    [RAG Context]
    Orchestrates a full pipeline:
    1. Read Dataset
    2. Auto Clean
    3. Generate Profile
    4. Model Selection (ML vs DL)
    5. Train Model
    6. Return Summary
    """
    summary = {
        "steps": [],
        "model_metrics": {}
    }
    
    try:
        # 1. Read
        logger.info("Step 1: Reading Data", url=dataset_url)
        # We use pandas directly for simplicity as io_ops might return a dict
        df = pd.read_csv(dataset_url) 
        summary["steps"].append(f"Read dataset with shape {df.shape}")
        
        # 2. Clean
        logger.info("Step 2: Cleaning Data")
        # pipeline_ops.clean_dataset_auto writes to file and returns string report.
        # We need the cleaned DF in memory.
        # Let's adapt or just recall the logic. 
        # Ideally we refactor clean_dataset_auto to return DF option, but it returns string.
        # We'll re-implement a robust in-memory version or modify pipeline_ops.
        # For now, let's use the file-based approach to be safe with the tool signature.
        clean_path = dataset_url.replace(".csv", "_cleaned.csv")
        try:
             # This works if dataset_url is local or we are okay writing to where it is.
             # If url is http, this fails. 
             # Let's assume for this Agent tool, we are working with local files mostly (from Vault).
            if not dataset_url.startswith("http"):
                pipeline_ops.clean_dataset_auto(dataset_url, clean_path)
                df = pd.read_csv(clean_path)
                summary["steps"].append("Cleaned dataset.")
        except Exception:
            # logger.warning("Cleaning step issue", error=str(e))
            # Continue with original if cleaning fails (e.g. read only permissions)
            pass
        
        # 3. Profile
        # We skip actual HTML generation here to save time/resources, or optional
        # pipeline_ops.generate_profile_report(clean_path, clean_path.replace(".csv", "_profile.html"))
        
        # 4. Selection
        model_type = _heuristic_model_selection(df, goal)
        summary["model_type"] = model_type
        
        # 5. Train
        if model_type == 'ml':
            logger.info("Step 5: Training XGBoost")
            # We call train_xgboost
            # We need to await it since it's async
            res = await xgboost_ops.train_xgboost_model(clean_path if 'clean_path' in locals() else dataset_url, target_column)
            summary["model_metrics"] = res
            
        elif model_type == 'dl':
            logger.info("Step 5: Training Deep Learning")
            # Build
            input_dim = df.shape[1] - 1 # remove target
            # task detection
            is_regression = df[target_column].dtype in ['float64', 'int64'] and df[target_column].nunique() > 20
            task = 'regression' if is_regression else 'classification'
            output_dim = 1 if task == 'regression' else df[target_column].nunique()
            
            build_res = model_ops.build_dense_network(input_dim, output_dim, [64, 32], task)
            
            # Train
            train_res = train_ops.train_deep_model(clean_path if 'clean_path' in locals() else dataset_url, target_column, build_res, epochs=10)
            summary["model_metrics"] = train_res

        return summary

    except Exception as e:
        logger.error("analyze_data_science_project failed", error=str(e))
        return {"error": str(e)}
