import pytest
import asyncio

try:
    from mcp_servers.numpy_server.server import NumpyServer
except ImportError:
    pytest.skip("Numpy dependencies missing", allow_module_level=True)

@pytest.mark.asyncio
async def test_numpy_operations():
    server = NumpyServer()
    handler = server._handlers.get("calculate_array")
    if handler:
        # Test mean
        res = await handler({"operation": "mean", "data": [1, 2, 3, 4, 5]})
        assert not res.isError
        assert "3.0" in res.content[0].text
