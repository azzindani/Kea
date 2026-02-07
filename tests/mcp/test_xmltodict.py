import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_xmltodict_server():
    """Verify XMLtoDict Server executes using MCP Client."""
    # Assuming xmltodict is required. If not, it might be built-in or vendored.
    # But for safety we add it.
    params = get_server_params("xmltodict_server", extra_dependencies=["xmltodict"])
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_res = await session.list_tools()
            tools = tools_res.tools
            print(f"\nDiscovered {len(tools)} tools via Client.")
            tool_names = [t.name for t in tools]
            assert "parse_xml_string" in tool_names
            print("XMLtoDict verification passed (Tools present).")
