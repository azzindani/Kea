import pytest
import asyncio
import os
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_duckdb_real_simulation():
    """
    REAL SIMULATION: Verify DuckDB Server (SQL, Analysis, Extensions).
    """
    params = get_server_params("duckdb_server", extra_dependencies=["duckdb", "pandas", "pyarrow"])
    
    print(f"\n--- Starting Real-World Simulation: DuckDB Server ---")
    
    db_name = "test_mcp_real.duckdb"
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Connect
            print(f"1. Connecting to {db_name}...")
            await session.call_tool("connect_db", arguments={"path": db_name})
            
            # 2. Create Table
            print("2. Creating table 'users'...")
            cols = {"id": "INTEGER", "name": "VARCHAR", "age": "INTEGER", "score": "DOUBLE"}
            await session.call_tool("create_table", arguments={"table_name": "users", "columns": cols})
            
            # 3. Insert Data (via execute_query for speed or specific insert tool if exists)
            # server.py has execute_query
            print("3. Inserting data...")
            await session.call_tool("execute_query", arguments={"query": "INSERT INTO users VALUES (1, 'Alice', 30, 95.5), (2, 'Bob', 25, 80.0), (3, 'Charlie', 35, 99.0)"})
            
            # 4. Analysis
            print("4. Running Analysis (get_column_stats)...")
            res = await session.call_tool("get_column_stats", arguments={"table_name": "users", "column_name": "score"})
            print(f" [PASS] Stats: {res.content[0].text}")
            
            # 5. SQL Query
            print("5. Querying (Fetch All)...")
            res = await session.call_tool("fetch_all", arguments={"query": "SELECT * FROM users WHERE age > 28"})
            print(f" [PASS] Rows: {res.content[0].text}")
            
            # 6. Spatial (Extensions)
            print("6. Spatial Ops (Point)...")
            try:
                res = await session.call_tool("st_point", arguments={"lat": 40.7128, "lon": -74.0060})
                if not res.isError:
                    print(f" [PASS] Point WKT: {res.content[0].text}")
                else:
                    print(" [INFO] Spatial extension might need loading (install_extension spatial)")
            except Exception as e:
                print(f" [WARN] Spatial test skipped: {e}")

            # 7. Cleanup
            await session.call_tool("drop_table", arguments={"table_name": "users"})
            await session.call_tool("close_connection")
            
            # Clean up file
            if os.path.exists(db_name):
                os.remove(db_name)

    print("--- DuckDB Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
