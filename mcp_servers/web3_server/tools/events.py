
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.web3_server.tools.network import get_web3_instance
from web3 import Web3

async def get_contract_events(arguments: dict) -> ToolResult:
    """
    Get Contract Events (Logs).
    Default: Search for Transfer events if no topic provided.
    """
    address = arguments.get("address")
    from_block = arguments.get("from_block", "latest")
    to_block = arguments.get("to_block", "latest")
    topics = arguments.get("topics") # List of strings (hashes)
    
    # If using block number relative (e.g. -100), need to handle logic
    # Here assume "latest" or exact number.
    
    try:
        w3 = await get_web3_instance(arguments)
        
        # If no topics, default to ERC20 Transfer: Transfer(address,address,uint256)
        if not topics:
            topics = [w3.keccak(text="Transfer(address,address,uint256)").hex()]
            
        logs = await w3.eth.get_logs({
            "address": w3.to_checksum_address(address) if address else None,
            "fromBlock": from_block,
            "toBlock": to_block,
            "topics": topics
        })
        
        # Summary
        return ToolResult(content=[TextContent(text=f"### Contract Events\n**Count**: {len(logs)}\n**Topics**: {topics}\n**Range**: {from_block}-{to_block}\n\nLogs (capped at 100K):\n{logs[:100000]}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
