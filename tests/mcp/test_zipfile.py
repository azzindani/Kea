import pytest
import asyncio
import os
import tempfile
import zipfile
from mcp_servers.zipfile_server.server import ZipfileServer

@pytest.mark.asyncio
async def test_zip_operations():
    server = ZipfileServer()
    handler = server._handlers.get("create_archive")
    if handler:
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            tmp_path = tmp.name
        try:
             with open("dummy.txt", "w") as f: f.write("content")
             res = await handler({"files": ["dummy.txt"], "output_path": tmp_path})
             assert not res.isError
             assert zipfile.is_zipfile(tmp_path)
        finally:
             if os.path.exists(tmp_path): os.remove(tmp_path)
             if os.path.exists("dummy.txt"): os.remove("dummy.txt")
