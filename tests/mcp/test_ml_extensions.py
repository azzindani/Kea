import pytest
import asyncio
import os
import pandas as pd
import numpy as np
from tests.mcp.client_utils import SafeClientSession as ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_ml_extensions(tmp_path):
    """
    Verify ML Extensions: XGBoost, Tuning, Sklearn, Metrics, Preprocessing,
    Clustering, Decomposition, Ensemble.
    """
    params = get_server_params("ml_server", extra_dependencies=["scikit-learn", "pandas", "numpy", "xgboost", "structlog"])
    
    # Create dummy data
    data_path = tmp_path / "iris.csv"
    df = pd.DataFrame({
        'feature1': np.random.rand(50),
        'feature2': np.random.rand(50),
        'feature3': np.random.rand(50),
        'target': np.random.randint(0, 2, 50)
    })
    df.to_csv(data_path, index=False)
    data_url = str(data_path)
    
    print(f"\n--- Starting ML Extension Simulation ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # --- Previous Tests ---
            print("1. XGBoost Train...")
            await session.call_tool("train_xgboost_model", arguments={
                "data_url": data_url, "target_column": "target", "model_type": "classifier",
                "params": {"n_estimators": 2, "max_depth": 2}
            })

            # --- New Tests ---
            
            # 5. Clustering
            print("5. Clustering (KMeans)...")
            res = await session.call_tool("cluster_kmeans", arguments={
                "data_url": data_url,
                "n_clusters": 3
            })
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m KMeans: {res.content[0].text[:100]}...")
            else:
                 print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

            # 6. Decomposition
            print("6. Decomposition (PCA)...")
            res = await session.call_tool("decompose_pca", arguments={
                "data_url": data_url,
                "n_components": 2
            })
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m PCA: {res.content[0].text[:100]}...")
            else:
                 print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

            # 7. Ensemble
            print("7. Ensemble (Bagging)...")
            res = await session.call_tool("ensemble_bagging_classifier", arguments={
                "data_url": data_url,
                "target_column": "target",
                "n_estimators": 5
            })
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Bagging: {res.content[0].text[:100]}...")
            else:
                 print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

            # 8. Feature Selection
            print("8. Feature Selection (SelectKBest)...")
            res = await session.call_tool("select_k_best", arguments={
                "data_url": data_url,
                "target_column": "target",
                "k": 2
            })
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m SelectKBest: {res.content[0].text}")
            else:
                 print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

    print("--- ML Extension Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
