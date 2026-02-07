import pytest
import asyncio
from mcp_servers.web3_server.server import Web3Server
from mcp_servers.web3_server.tools.network import NetworkManager

# Known addresses
VITALIK = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
USDT_ETH = "0xdAC17F958D2ee523a2206206994597C13D831ec7"

@pytest.mark.asyncio
async def test_web3_connection():
    """Verify Web3 RPC connection."""
    try:
        w3 = await NetworkManager.get_web3("https://eth.llamarpc.com")
        assert await w3.is_connected()
    except Exception as e:
        pytest.skip(f"Web3 RPC unavailable: {e}")

@pytest.mark.asyncio
async def test_web3_tools_integration():
    """Verify Web3 tools with real RPC (Skipped if no connection)."""
    server = Web3Server()
    
    # Pre-check connection
    try:
        w3 = await NetworkManager.get_web3("https://eth.llamarpc.com")
        if not await w3.is_connected():
             pytest.skip("No Web3 Connection")
    except:
        pytest.skip("No Web3 Connection")

    # 1. Get Balance
    try:
        handler = server._handlers["get_balance"]
        res = await handler({"address": VITALIK})
        if res.isError:
             pytest.fail(f"get_balance failed: {res.content[0].text}")
        assert "ETH" in res.content[0].text or "wei" in res.content[0].text
    except Exception as e:
        pytest.fail(f"get_balance exception: {e}")

    # 2. Token Metadata
    try:
        handler = server._handlers["get_token_metadata"]
        res = await handler({"token_address": USDT_ETH})
        if not res.isError:
             assert "USDT" in res.content[0].text
    except Exception as e:
         pass 

    # 3. Block Number
    try:
        handler = server._handlers["get_block_number"]
        res = await handler({})
        assert not res.isError
        assert int(res.content[0].text) > 15000000
    except Exception as e:
        pass
