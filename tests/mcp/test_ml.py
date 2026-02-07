import pytest
import asyncio

try:
    from mcp_servers.ml_server.server import MLServer
except ImportError:
    pytest.skip("ML dependencies missing", allow_module_level=True)

@pytest.mark.asyncio
async def test_ml_server_train():
    """Test ML Server basic training simulation."""
    server = MLServer()
    # Mock data for training
    data = [{"feature1": 1, "target": 0}, {"feature1": 2, "target": 1}]
    try:
        handler = server._handlers.get("train_model")
        if handler:
            res = await handler({"data": data, "target_column": "target"})
            assert not res.isError
            assert "model_id" in res.content[0].text
    except Exception as e:
        pytest.fail(f"ML Server failed: {e}")
