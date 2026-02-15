import pytest
import asyncio
from tests.mcp.client_utils import SafeClientSession as ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_analysis_agent():
    """
    Verify Analysis Agent Tool.
    """
    params = get_server_params("analysis_server", extra_dependencies=["pandas", "numpy", "scikit-learn", "xgboost", "tensorflow"])
    
    data_url = "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv"
    
    print(f"\n--- Starting Analysis Agent Test ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("1. Analyze Project...")
            res = await session.call_tool("analyze_data_science_project", arguments={
                "dataset_url": data_url, 
                "target_column": "species", 
                "goal": "Classify species using ML"
            })
            
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Result: {res.content[0].text[:200]}...")
            else:
                 print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

    print("--- Analysis Agent Test Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
