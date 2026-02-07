import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_ccxt_server():
    """Verify CCXT Server executes using MCP Client."""
    
    # CCXT server needs ccxt and pandas
    params = get_server_params("ccxt_server", extra_dependencies=["ccxt", "pandas"])
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Discover Tools
            tools_res = await session.list_tools()
            tools = tools_res.tools
            print(f"\nDiscovered {len(tools)} tools via Client.")
            
            tool_names = [t.name for t in tools]
            # Check for critical tools
            assert "get_ticker" in tool_names
            assert "get_ohlcv" in tool_names
            
            print("CCXT verification passed (Tools present).")
