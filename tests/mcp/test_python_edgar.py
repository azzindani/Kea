import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_python_edgar_server():
    """Verify Python Edgar Server executes using MCP Client."""
    params = get_server_params("python_edgar_server", extra_dependencies=["edgartools", "pandas"])
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_res = await session.list_tools()
            tools = tools_res.tools
            print(f"\nDiscovered {len(tools)} tools via Client.")
            tool_names = [t.name for t in tools]
            assert "find_filings" in tool_names
            print("Python Edgar verification passed (Tools present).")
