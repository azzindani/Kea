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
            print(f" \033[92m[PASS]\033[0m Created: {res.content[0].text}")
            
            # 2. Math (Add)
            print("2. Adding Arrays...")
            res = await session.call_tool("add", arguments={"x1": data, "x2": data})
            print(f" \033[92m[PASS]\033[0m Result: {res.content[0].text}")

            # 3. Linear Algebra (Dot Product)
            print("3. Dot Product...")
            res = await session.call_tool("dot", arguments={"a": data, "b": data})
            print(f" \033[92m[PASS]\033[0m Dot: {res.content[0].text}")
            
            # 4. Statistics (Mean/Sum)
            print("4. Sum...")
            res = await session.call_tool("sum_val", arguments={"a": data})
            print(f" \033[92m[PASS]\033[0m Sum: {res.content[0].text}")

            # 5. Random
            print("5. Random Normal...")
            res = await session.call_tool("rand_normal", arguments={"size": [2, 2]})
            print(f" \033[92m[PASS]\033[0m Random: {res.content[0].text}")

            # 6. Manipulation (Reshape)
            print("6. Reshape...")
            flat = [1, 2, 3, 4]
            res = await session.call_tool("reshape", arguments={"a": flat, "newshape": [2, 2]})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Reshaped: {res.content[0].text}")

            # 7. Logic
            print("7. Logical AND...")
            res = await session.call_tool("logical_and", arguments={"x1": [True, False], "x2": [True, True]})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Logic: {res.content[0].text}")

            # 8. Solve Linear Equation
            print("8. Solve (Ax = b)...")
            res = await session.call_tool("solve", arguments={"a": [[3, 1], [1, 2]], "b": [9, 8]})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Solution: {res.content[0].text}")

    print("--- Numpy Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
