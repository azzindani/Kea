
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.web3_server.tools.network import get_web3_instance

async def resolve_ens(arguments: dict) -> ToolResult:
    """
    Resolve ENS Name to Address.
    """
    name = arguments.get("name") # "vitalik.eth"
    
    try:
        w3 = await get_web3_instance(arguments)
        
        # ENS usually only works on Mainnet
        # Check chain id? Or just try
        address = await w3.ens.address(name)
        
        if address:
             return ToolResult(content=[TextContent(text=f"### ENS Resolution\n**Name**: {name}\n**Address**: {address}")])
        else:
             return ToolResult(content=[TextContent(text=f"ENS Name '{name}' not found.")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
