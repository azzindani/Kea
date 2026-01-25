
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.web3_server.tools.network import get_web3_instance

async def get_ens_reverse_record(arguments: dict) -> ToolResult:
    """
    Get ENS Name for an Address (Reverse Resolution).
    """
    address = arguments.get("address")
    
    try:
        w3 = await get_web3_instance(arguments)
        
        # Check cache/network first?
        # w3.ens.name() requires connection to mainnet, usually handled by provider
        name = await w3.ens.name(w3.to_checksum_address(address))
        
        if name:
             return ToolResult(content=[TextContent(text=f"### ENS Reverse Lookkup\n**Address**: {address}\n**Name**: {name}")])
        else:
             return ToolResult(content=[TextContent(text=f"No ENS name found for {address}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
