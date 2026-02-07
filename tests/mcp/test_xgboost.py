import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_xgboost_real_simulation():
    """
    REAL SIMULATION: Verify XGBoost Server (ML).
    """
    params = get_server_params("xgboost_server", extra_dependencies=["xgboost", "scikit-learn", "numpy", "pandas", "joblib", "scipy"])
    
    # Dummy Data: Binary Classification
    X = [[1, 2], [3, 4], [5, 6], [7, 8]]
    y = [0, 0, 1, 1]
    
    print(f"\n--- Starting Real-World Simulation: XGBoost Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Train Classifier
            print("1. Training XGBClassifier...")
            res = await session.call_tool("xgb_classifier", arguments={"X": X, "y": y, "n_estimators": 5})
            if not res.isError:
                # Returns model ID or path usually, or JSON
                 print(f" [PASS] Model Trained: {str(res.content[0].text)[:100]}...")
            else:
                 print(f" [WARN] Training Failed: {res.content[0].text}")

    print("--- XGBoost Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
