import pytest
import asyncio
import os
import pandas as pd
from tests.mcp.client_utils import SafeClientSession as ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_pandas_extensions():
    """
    Verify Pandas Extensions: Bulk Ops & Pipeline Ops.
    """
    params = get_server_params("pandas_server", extra_dependencies=["pandas", "numpy", "structlog", "ydata-profiling", "requests", "openpyxl", "scikit-learn"])
    
    # Setup test files
    df1 = pd.DataFrame({"id": [1, 2], "val": ["A", "B"]})
    df2 = pd.DataFrame({"id": [2, 3], "val": ["C", "D"]})
    f1 = "ext_test_1.csv"
    f2 = "ext_test_2.csv"
    df1.to_csv(f1, index=False)
    df2.to_csv(f2, index=False)
    
    print(f"\n--- Starting Pandas Extension Simulation ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Bulk Merge
            print("1. Bulk Merge...")
            res = await session.call_tool("merge_datasets_bulk", arguments={
                "file_paths": [f1, f2],
                "on": "id", 
                "how": "outer",
                "output_path": "ext_merged.csv"
            })
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Merge: {res.content[0].text[:100]}...")
            else:
                 print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

            # 2. Pipeline Clean
            print("2. Auto Clean...")
            # Dirty DF
            df_dirty = pd.DataFrame({"  Col A ": [" x ", "y", None], "Col-B": [1, 1000, 2]})
            f_dirty = "ext_dirty.csv"
            df_dirty.to_csv(f_dirty, index=False)
            
            res = await session.call_tool("clean_dataset_auto", arguments={
                "file_path": f_dirty,
                "output_path": "ext_clean.csv"
            })
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Clean Report:\n{res.content[0].text[:200]}...")
            else:
                 print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

    print("--- Pandas Extension Simulation Complete ---")
    
    # Cleanup
    for f in [f1, f2, "ext_merged.csv", f_dirty, "ext_clean.csv"]:
        if os.path.exists(f):
            os.remove(f)

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
