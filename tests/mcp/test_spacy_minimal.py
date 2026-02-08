import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_spacy_minimal():
    """
    Minimal test to isolate Spacy crash.
    """
    params = get_server_params("spacy_server", extra_dependencies=["spacy", "pandas", "matplotlib"])
    
    text = "Apple is looking at buying U.K. startup for $1 billion."
    
    print(f"\n--- Starting Minimal Simulation ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Initialized.")
            
            # 1. Load Model
            print("1. Loading Model...")
            await session.call_tool("load_model", arguments={"model_name": "en_core_web_sm"})
            print("Loaded.")
            
            # 2. Entities
            print("2. Entities...")
            res = await session.call_tool("get_entities", arguments={"text": text})
            print(f"Entities: {res.content[0].text}")

    print("--- Minimal Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
