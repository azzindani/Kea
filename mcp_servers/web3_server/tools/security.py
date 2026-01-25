
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.web3_server.tools.network import get_web3_instance

async def simulate_transaction(arguments: dict) -> ToolResult:
    """
    Simulate Transaction (Dry Run) to check for Reverts.
    Requires: to_address, value (optional), data (optional), from_address (optional).
    """
    to_address = arguments.get("to_address")
    from_address = arguments.get("from_address") # Optional (uses Zero address if None)
    value = arguments.get("value", 0) # ETH amount
    data = arguments.get("data", "0x")
    
    try:
        w3 = await get_web3_instance(arguments)
        
        tx = {
            'to': w3.to_checksum_address(to_address),
            'value': w3.to_wei(float(value), 'ether'),
            'data': data
        }
        if from_address:
            tx['from'] = w3.to_checksum_address(from_address)
            
        # eth_call executes without broadcasting
        # If it reverts, it usually raises an exception or returns revert data string
        try:
            result = await w3.eth.call(tx)
            return ToolResult(content=[TextContent(text=f"### Simulation SUCCESS\n**Result**: {result.hex()}\n**Status**: Likely Success (No Revert).")])
        except Exception as e:
             return ToolResult(content=[TextContent(text=f"### Simulation REVERT\n**Error**: {str(e)}\n**Status**: Transaction will fail.")])
             
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
