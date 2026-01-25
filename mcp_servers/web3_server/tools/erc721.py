
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.web3_server.tools.network import get_web3_instance
from web3 import Web3

# Minimal ERC721 ABI
ERC721_ABI = [
    {"constant":True,"inputs":[{"name":"_tokenId","type":"uint256"}],"name":"ownerOf","outputs":[{"name":"owner","type":"address"}],"type":"function"},
    {"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},
    {"constant":True,"inputs":[{"name":"_tokenId","type":"uint256"}],"name":"tokenURI","outputs":[{"name":"","type":"string"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"}
]

async def get_nft_owner(arguments: dict) -> ToolResult:
    """
    Get NFT Owner (ERC721).
    """
    token_address = arguments.get("token_address")
    token_id = int(arguments.get("token_id"))
    
    try:
        w3 = await get_web3_instance(arguments)
        contract = w3.eth.contract(address=w3.to_checksum_address(token_address), abi=ERC721_ABI)
        
        owner = await contract.functions.ownerOf(token_id).call()
        
        return ToolResult(content=[TextContent(text=f"### NFT Owner\n**Contract**: {token_address}\n**ID**: {token_id}\n**Owner**: {owner}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_nft_metadata_uri(arguments: dict) -> ToolResult:
    """
    Get NFT Token URI.
    """
    token_address = arguments.get("token_address")
    token_id = int(arguments.get("token_id"))
    
    try:
        w3 = await get_web3_instance(arguments)
        contract = w3.eth.contract(address=w3.to_checksum_address(token_address), abi=ERC721_ABI)
        
        uri = await contract.functions.tokenURI(token_id).call()
        
        return ToolResult(content=[TextContent(text=f"### NFT URI\n**Contract**: {token_address}\n**ID**: {token_id}\n**URI**: {uri}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
