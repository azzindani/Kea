import pytest
import asyncio
import os
import tempfile
from mcp_servers.docx_server.server import DocxServer

@pytest.mark.asyncio
async def test_docx_create():
    server = DocxServer()
    handler = server._handlers.get("create_document")
    if handler:
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            res = await handler({"content": "Hello World", "path": tmp_path})
            assert not res.isError
            assert os.path.exists(tmp_path)
            # Verify read
            read_handler = server._handlers.get("read_document")
            if read_handler:
                res_read = await read_handler({"path": tmp_path})
                assert "Hello" in res_read.content[0].text
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
