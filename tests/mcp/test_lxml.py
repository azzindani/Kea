import pytest
import asyncio
from mcp_servers.lxml_server.server import LxmlServer

@pytest.mark.asyncio
async def test_lxml_parse():
    lxml_server = LxmlServer()
    l_handler = lxml_server._handlers.get("parse_xml")
    if l_handler:
        res = await l_handler({"xml_content": "<root><a>1</a></root>"})
        assert not res.isError
