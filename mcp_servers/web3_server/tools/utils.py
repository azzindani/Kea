
from shared.mcp.protocol import ToolResult, TextContent
from web3 import Web3

async def to_wei(arguments: dict) -> ToolResult:
    """
    Convert value (ether/gwei) to Wei.
    """
    amount = arguments.get("amount")
    unit = arguments.get("unit", "ether")
    
    try:
        val = Web3.to_wei(amount, unit)
        return ToolResult(content=[TextContent(text=f"{amount} {unit} = {val} wei")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def from_wei(arguments: dict) -> ToolResult:
    """
    Convert Wei to value (ether/gwei).
    """
    amount = arguments.get("amount")
    unit = arguments.get("unit", "ether")
    
    try:
        val = Web3.from_wei(int(amount), unit)
        return ToolResult(content=[TextContent(text=f"{amount} wei = {val} {unit}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
