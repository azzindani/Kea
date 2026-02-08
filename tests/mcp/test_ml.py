import pytest
import asyncio
from tests.mcp.client_utils import SafeClientSession as ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_ml_real_simulation():
    """
    REAL SIMULATION: Verify ML Server (AutoML, Clustering).
    """
    params = get_server_params("ml_server", extra_dependencies=["scikit-learn", "pandas", "numpy"])
    
    # Iris dataset URL
    data_url = "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv"
    
    print(f"\n--- Starting Real-World Simulation: ML Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Feature Importance
            print("1. Feature Importance (Target: species)...")
            res = await session.call_tool("feature_importance", arguments={"data_url": data_url, "target_column": "species"})
            if not res.isError:
                print(f" \033[92m[PASS]\033[0m Importance: {res.content[0].text}")
            else:
                print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

            # 2. Clustering
            print("2. Clustering (KMeans, k=3)...")
            res = await session.call_tool("convert_clustering", arguments={"data_url": data_url, "n_clusters": 3})
            if not res.isError:
                print(f" \033[92m[PASS]\033[0m Clusters: {res.content[0].text[:1000]}...")

            # 3. Anomaly Detection
            print("3. Anomaly Detection...")
            res = await session.call_tool("anomaly_detection", arguments={"data_url": data_url})
            if not res.isError:
                print(f" \033[92m[PASS]\033[0m Anomalies: {res.content[0].text[:1000]}...")

            # 4. Time Series Forecast
            print("4. Forecasting...")
            # Using simple generated data URL or data structure if tool supports it.
            # Tool signature says data_url is required.
            # Let's use the same data_url but forecast 'sepal_length' (treated as series)
            res = await session.call_tool("time_series_forecast", arguments={"data_url": data_url, "value_column": "sepal_length", "periods": 5})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Forecast: {res.content[0].text[:1000]}...")

    print("--- ML Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
