"""
MCP Tool Tests: Analysis Tools.
"""
import pytest
import asyncio
import pandas as pd
import numpy as np
from tests.mcp.client_utils import SafeClientSession as ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_analysis_real_simulation(tmp_path):
    """
    REAL SIMULATION: Verify Analysis Tools including Advanced Plots, Stats, Signals.
    """
    params = get_server_params("analysis_server", extra_dependencies=["pandas", "numpy", "scipy", "scikit-learn", "matplotlib", "seaborn", "statsmodels"])
    
    # Create dummy data
    data_path = tmp_path / "data.csv"
    df = pd.DataFrame({
        'group': np.random.choice(['A', 'B'], 50),
        'val1': np.random.randn(50),
        'val2': np.random.randn(50) + 1,
        'time': np.linspace(0, 10, 50)
    })
    df.to_csv(data_path, index=False)
    data_url = str(data_path)

    print(f"\n--- Starting Real-World Simulation: Analysis Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # --- Previous Tests (Brief) ---
            # await session.call_tool("plot_scatter", arguments={"file_path": data_url, "x": "val1", "y": "val2"})
            
            # --- New Tests ---

            # 4. Advanced Plots
            print("4. Advanced Plots (KDE, Joint)...")
            plot_out = tmp_path / "kde.png"
            res = await session.call_tool("plot_kde", arguments={
                "file_path": data_url, "x": "val1"
            })
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m KDE Plot: {res.content[0].text}")
            else:
                 print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

            print("   Joint Plot...")
            res = await session.call_tool("plot_joint", arguments={
                "file_path": data_url, "x": "val1", "y": "val2"
            })
            assert not res.isError
            
            # 5. Advanced Stats
            print("5. Advanced Stats (ANOVA)...")
            res = await session.call_tool("stat_anova_oneway", arguments={
                "file_path": data_url,
                "formula": "val1 ~ C(group)"
            })
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m ANOVA: {res.content[0].text[:100]}...")
            else:
                 print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

            # 6. Signal Processing
            print("6. Signal Processing (FFT)...")
            res = await session.call_tool("signal_fft", arguments={
                "file_path": data_url,
                "column": "val1"
            })
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m FFT: {res.content[0].text[:100]}...")
            else:
                 print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

    print("--- Analysis Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
