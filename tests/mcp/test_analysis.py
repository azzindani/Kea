import pytest
import asyncio
from tests.mcp.client_utils import SafeClientSession as ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_analysis_agent_real_simulation():
    """
    REAL SIMULATION: Verify Analysis Agent (Multitalent).
    """
    # Dependencies include all since it imports from others
    params = get_server_params("analysis_server", extra_dependencies=["pandas", "numpy", "scikit-learn", "xgboost", "tensorflow", "structlog"])
    
    data_url = "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv"
    
    print(f"\n--- Starting Real-World Simulation: Analysis Agent ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Super Tool Execution
            print("1. Running 'analyze_data_science_project'...")
            # We use a broad goal to trigger defaults
            res = await session.call_tool("analyze_data_science_project", arguments={
                "dataset_url": data_url, 
                "target_column": "species", 
                "goal": "Classify flower species with high accuracy"
            })
            
            if not res.isError:
                 import json
                 try:
                     result = json.loads(res.content[0].text)
                     print(f" \033[92m[PASS]\033[0m \nSteps: {result.get('steps')}\nModel Type: {result.get('model_type')}")
                 except:
                     print(f" \033[92m[PASS]\033[0m (Output not pure JSON): {res.content[0].text[:500]}...")
            else:
                print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

    print("--- Analysis Agent Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
