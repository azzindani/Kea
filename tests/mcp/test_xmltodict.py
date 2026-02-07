import pytest
import asyncio
from mcp_servers.xmltodict_server.server import XmltodictServer

@pytest.mark.asyncio
async def test_xml_to_dict():
    server = XmltodictServer()
    handler = server._handlers.get("xml_to_dict")
    if handler:
         xml = "<root><key>value</key></root>"
         res = await handler({"xml_content": xml})
         assert not res.isError
         assert "value" in res.content[0].text
