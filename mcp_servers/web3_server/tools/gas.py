
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.web3_server.tools.network import get_web3_instance

async def estimate_gas(arguments: dict) -> ToolResult:
    """
    Estimate Gas for a transaction call.
    """
    to_address = arguments.get("to_address")
    from_address = arguments.get("from_address")
    data = arguments.get("data", "0x")
    value = arguments.get("value", 0)
    
    try:
        w3 = await get_web3_instance(arguments)
        
        tx = {
            'to': w3.to_checksum_address(to_address),
            'from': w3.to_checksum_address(from_address) if from_address else None,
            'data': data,
            'value': int(value)
        }
        
        gas_estimate = await w3.eth.estimate_gas(tx)
        
        return ToolResult(content=[TextContent(text=f"### Gas Estimate\n**Gas**: {gas_estimate}\n**Tx**: {tx}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
