
import pytest
import asyncio
import sys
from unittest.mock import MagicMock, patch, AsyncMock

# Mock langgraph BEFORE importing graph
mock_langgraph = MagicMock()
sys.modules["langgraph"] = mock_langgraph
sys.modules["langgraph.graph"] = mock_langgraph

from services.orchestrator.mcp.client import MCPOrchestrator, get_mcp_orchestrator
from services.orchestrator.core.graph import researcher_node

@pytest.mark.asyncio
async def test_mcp_orchestrator_singleton():
    """Verify singleton pattern works."""
    # Reset singleton
    MCPOrchestrator._instance = None
    
    instance1 = get_mcp_orchestrator()
    instance2 = get_mcp_orchestrator()
    instance3 = MCPOrchestrator()
    
    assert instance1 is instance2
    assert instance1 is instance3
    assert instance1._initialized is True
    
    # Verify initialization only happens once
    instance1._tool_registry["test"] = "server"
    assert instance2._tool_registry["test"] == "server"

@pytest.mark.asyncio
async def test_researcher_node_calls_mcp():
    """Verify researcher_node uses MCP client to call tools."""
    
    # Mock the singleton
    mock_client = MagicMock(spec=MCPOrchestrator)
    mock_client.call_tool = AsyncMock()
    
    # Mock return value
    mock_result = MagicMock()
    mock_result.isError = False
    mock_content = MagicMock()
    mock_content.text = "Mock search result with (https://example.com)"
    mock_result.content = [mock_content]
    mock_client.call_tool.return_value = mock_result
    
    # Inject mock into mcp.client
    with patch("services.orchestrator.mcp.client.get_mcp_orchestrator", return_value=mock_client):
        
        state = {
            "query": "test query",
            "sub_queries": ["sub query 1"],
            "facts": [],
            "sources": []
        }
        
        result_state = await researcher_node(state)
        
        # Verify call_tool was called
        mock_client.call_tool.assert_called()
        args = mock_client.call_tool.call_args
        assert args[0][0] == "web_search"
        assert args[0][1]["query"] == "sub query 1"
        
        # Verify facts were extracted
        assert len(result_state["facts"]) > 0
        assert "Mock search result" in result_state["facts"][0]["text"]
        assert result_state["sources"][0]["url"] == "https://example.com"

@pytest.mark.asyncio
async def test_stop_servers_robustness():
    """Verify stop_servers handles hung processes."""
    client = get_mcp_orchestrator()
    client._servers = {}
    
    # Mock a server connection with a hung process
    mock_process = MagicMock()
    mock_process.terminate = MagicMock()
    # First wait raises TimeoutExpired
    import subprocess
    mock_process.wait.side_effect = [subprocess.TimeoutExpired(cmd="test", timeout=1), None]
    mock_process.kill = MagicMock()
    
    mock_conn = MagicMock()
    mock_conn.process = mock_process
    mock_conn.client = AsyncMock()
    # Mock client close hanging slightly but finishing
    mock_conn.client.close.return_value = None
    
    client._servers["hung_server"] = mock_conn
    
    await client.stop_servers()
    
    # Verify terminate AND kill were called
    mock_process.terminate.assert_called_once()
    mock_process.kill.assert_called_once()
    assert len(client._servers) == 0
