
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.web3_server.tools.network import get_web3_instance
from web3 import Web3
from datetime import datetime

AGGREGATOR_V3_ABI = [
    {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"description","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"latestRoundData","outputs":[{"internalType":"uint80","name":"roundId","type":"uint80"},{"internalType":"int256","name":"answer","type":"int256"},{"internalType":"uint256","name":"startedAt","type":"uint256"},{"internalType":"uint256","name":"updatedAt","type":"uint256"},{"internalType":"uint80","name":"answeredInRound","type":"uint80"}],"stateMutability":"view","type":"function"}
]

async def get_chainlink_price(arguments: dict) -> ToolResult:
    """
    Get Oracle Price from Chainlink Feed.
    Requires Feed Address.
    """
    feed_address = arguments.get("feed_address")
    
    try:
        w3 = await get_web3_instance(arguments)
        feed = w3.eth.contract(address=w3.to_checksum_address(feed_address), abi=AGGREGATOR_V3_ABI)
        
        decimals = await feed.functions.decimals().call()
        description = await feed.functions.description().call()
        data = await feed.functions.latestRoundData().call()
        
        # data[1] is answer
        price = float(data[1]) / (10 ** decimals)
        updated_at = datetime.fromtimestamp(data[3])
        
        return ToolResult(content=[TextContent(text=f"### Chainlink Oracle\n**Feed**: {description}\n**Price**: {price}\n**Updated**: {updated_at}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
