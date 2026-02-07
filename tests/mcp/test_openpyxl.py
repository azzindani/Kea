import pytest
import asyncio
import os
import tempfile
from mcp_servers.openpyxl_server.server import OpenpyxlServer

@pytest.mark.asyncio
async def test_openpyxl_create():
    server = OpenpyxlServer()
    handler = server._handlers.get("create_spreadsheet")
    if handler:
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            data = {"Sheet1": [["A", "B"], [1, 2]]}
            res = await handler({"data": data, "path": tmp_path})
            assert not res.isError
            assert os.path.exists(tmp_path)
        finally:
             if os.path.exists(tmp_path):
                os.remove(tmp_path)
