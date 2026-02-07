import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_shutil_server():
    """Verify Shutil Server executes using MCP Client."""
    params = get_server_params("shutil_server", extra_dependencies=["pandas"])
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_res = await session.list_tools()
            tools = tools_res.tools
            print(f"\nDiscovered {len(tools)} tools via Client.")
            tool_names = [t.name for t in tools]
            # Supports copy_file or maybe different names
            assert "copy_file" in tool_names or "copy_file_2" in tool_names
            print("Shutil verification passed (Tools present).")
