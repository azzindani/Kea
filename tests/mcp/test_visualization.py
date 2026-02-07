import pytest
import asyncio
import pandas as pd
import os
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_visualization_real_simulation():
    """
    REAL SIMULATION: Verify Visualization Server (Plotly).
    """
    params = get_server_params("visualization_server", extra_dependencies=["plotly", "pandas", "numpy", "kaleido"])
    
    # Create dummy data CSV
    csv_path = "test_viz_data.csv"
    df = pd.DataFrame({
        "x": range(10),
        "y": [i**2 for i in range(10)],
        "category": ["A", "B"] * 5
    })
    df.to_csv(csv_path, index=False)
    abs_path = os.path.abspath(csv_path)
    
    print(f"\n--- Starting Real-World Simulation: Visualization Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Create Plotly Chart
            print("1. Creating Scatter Plot...")
            # Server expects data_url (file path or URL)
            res = await session.call_tool("create_plotly_chart", arguments={
                "data_url": abs_path,
                "chart_type": "scatter",
                "x_column": "x",
                "y_column": "y",
                "color_column": "category",
                "title": "Test Scatter"
            })
            if not res.isError:
                 print(f" [PASS] Chart Created (Length: {len(res.content[0].text)})")
            
            # 2. Correlation Heatmap
            print("2. Creating Heatmap...")
            res = await session.call_tool("create_correlation_heatmap", arguments={"data_url": abs_path})
            if not res.isError:
                 print(f" [PASS] Heatmap Created")

    # Cleanup
    if os.path.exists(csv_path):
        os.remove(csv_path)

    print("--- Visualization Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
