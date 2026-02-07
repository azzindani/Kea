import pytest
import asyncio
from mcp_servers.duckdb_server.server import DuckDBServer

@pytest.mark.asyncio
async def test_duckdb_query():
    server = DuckDBServer()
    handler = server._handlers.get("execute_query")
    if handler:
        # In-memory query
        res = await handler({"query": "SELECT 1 + 1 as result"})
        assert not res.isError
        assert "2" in str(res.content[0].text)
