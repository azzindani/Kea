import pytest
import asyncio
import json
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_numpy_real_simulation():
    """
    REAL SIMULATION: Verify Numpy Server (Math, Linear Algebra).
    """
    params = get_server_params("numpy_server", extra_dependencies=["numpy", "pandas"])
    
    print(f"\n--- Starting Real-World Simulation: Numpy Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Create Array
            print("1. Creating Array...")
            data = [[1, 2], [3, 4]]
            res = await session.call_tool("create_array", arguments={"data": data})
            print(f" [PASS] Created: {res.content[0].text}")
            
            # 2. Math (Add)
            print("2. Adding Arrays...")
            res = await session.call_tool("add", arguments={"x1": data, "x2": data})
            print(f" [PASS] Result: {res.content[0].text}")

            # 3. Linear Algebra (Dot Product)
            print("3. Dot Product...")
            res = await session.call_tool("dot", arguments={"a": data, "b": data})
            print(f" [PASS] Dot: {res.content[0].text}")
            
            # 4. Statistics (Mean/Sum)
            print("4. Sum...")
            res = await session.call_tool("sum_val", arguments={"a": data})
            print(f" [PASS] Sum: {res.content[0].text}")

            # 5. Random
            print("5. Random Normal...")
            res = await session.call_tool("rand_normal", arguments={"size": [2, 2]})
            print(f" [PASS] Random: {res.content[0].text}")

    print("--- Numpy Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
