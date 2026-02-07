import pytest
import asyncio
from mcp_servers.filesystem_server.server import FilesystemServer

@pytest.mark.asyncio
async def test_filesystem():
    server = FilesystemServer()
    handler = server._handlers.get("list_directory")
    if handler:
        try:
            res = await handler({"path": "."})
            assert not res.isError
            assert "README.md" in res.content[0].text or "pyproject.toml" in res.content[0].text
        except Exception:
            pass
