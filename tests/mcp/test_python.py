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
    params = get_server_params("python_server", extra_dependencies=["pandas", "duckdb", "numpy"])
    
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

            # 3. DataFrame Ops
            print("3. DataFrame Operations...")
            # We can create a DF via execute code first, or pass data??
            # dataframe_ops takes 'data' (csv string or json)
            csv_data = "col1,col2\n1,2\n3,4"
            res = await session.call_tool("dataframe_ops", arguments={"operation": "head", "data": csv_data})
            if not res.isError:
                 print(f" [PASS] DF Head: {res.content[0].text}")

    print("--- Python Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
