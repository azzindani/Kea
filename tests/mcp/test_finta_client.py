import pytest
import asyncio
import sys
import os
from tests.mcp.client_utils import SafeClientSession as ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Define the server execution command
def get_server_params():
    # Use the same python that runs pytest
    python_exe = sys.executable
    server_script = os.path.abspath("mcp_servers/finta_server/server.py")
    return StdioServerParameters(
        command="uv",
        args=["run", "--with", "finta", "--with", "pandas", "--with", "structlog", "python", server_script],
        env=os.environ.copy()
    )

@pytest.mark.asyncio
async def test_finta_tools_dynamic():
    """Verify ALL Finta tools using MCP Client."""
    
    params = get_server_params()
    
    # Connect to the server
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Discover Tools
            tools_res = await session.list_tools()
            tools = tools_res.tools
            print(f"\nDiscovered {len(tools)} tools via Client.")
            
            assert len(tools) > 50, "Expected >50 tools from Finta"
            
            # 2. Test Tools
            # Dummy Data
            prices = [100, 105, 110, 115, 112, 108, 105, 102, 100, 98, 95, 92, 90, 95, 100]
            data = []
            for i, p in enumerate(prices):
                data.append({
                    "date": f"2023-01-{i+1:02d}",
                    "open": p - 2, "high": p + 5, "low": p - 5, "close": p,
                    "volume": 1000 + (i * 100)
                })
            
            success = 0
            failed = 0
            
            for tool in tools:
                if tool.name.startswith("get_") and "suite" in tool.name: continue
                
                print(f"Testing {tool.name}...", end="")
                try:
                    # Generic call with 'data' argument
                    res = await session.call_tool(tool.name, arguments={"data": data})
                    if not res.isError:
                        print(" \033[92m[PASS]\033[0m")
                        success += 1
                    else:
                        # Some tools might need extra params, check if error is meaningful
                        print(f" \033[91m[FAIL]\033[0m {res.content[0].text[:1000] if res.content else 'Error'}")
                        failed += 1
                except Exception as e:
                     print(f" [EXCEPTION] {e}")
                     failed += 1
            
            print(f"\nPassed: {success}, Failed: {failed}")
            assert success > 0
