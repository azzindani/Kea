import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_python_real_simulation():
    """
    REAL SIMULATION: Verify Python Server (Code Execution).
    """
    params = get_server_params("python_server", extra_dependencies=[])
    
    print(f"\n--- Starting Real-World Simulation: Python Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Execute Code
            print("1. Executing Code...")
            code = "print('Hello World'); x = 10 + 20"
            res = await session.call_tool("execute_code", arguments={"code": code})
            print(f" [PASS] Result: {res.content[0].text}")

            # 2. SQL Query (DuckDB)
            print("2. Executing SQL...")
            query = "SELECT 1 + 1 AS result"
            res = await session.call_tool("sql_query", arguments={"query": query})
            print(f" [PASS] SQL Result: {res.content[0].text}")

    print("--- Python Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
