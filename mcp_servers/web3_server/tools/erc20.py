
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.web3_server.tools.network import get_web3_instance
from web3 import Web3

# Minimal ERC20 ABI
ERC20_ABI = [
    {"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"type":"function"}
]

async def get_token_balance(arguments: dict) -> ToolResult:
    """
    Get ERC20 Token Balance.
    """
    token_address = arguments.get("token_address")
    wallet_address = arguments.get("wallet_address")
    
    try:
        w3 = await get_web3_instance(arguments)
        
        token_contract = w3.eth.contract(address=w3.to_checksum_address(token_address), abi=ERC20_ABI)
        wallet = w3.to_checksum_address(wallet_address)
        
        # Async calls
        balance_wei = await token_contract.functions.balanceOf(wallet).call()
        try:
            decimals = await token_contract.functions.decimals().call()
        except:
            decimals = 18 # Fallback
            
        try:
            symbol = await token_contract.functions.symbol().call()
        except:
            symbol = "???"
            
        balance_fmt = balance_wei / (10 ** decimals)
        
        return ToolResult(content=[TextContent(text=f"### Token Balance\n**Symbol**: {symbol}\n**Balance**: {balance_fmt}\n**Raw**: {balance_wei}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_token_metadata(arguments: dict) -> ToolResult:
    """
    Get ERC20 Token Metadata (Name, Symbol, Decimals).
    """
    token_address = arguments.get("token_address")
    
    try:
        w3 = await get_web3_instance(arguments)
        token_contract = w3.eth.contract(address=w3.to_checksum_address(token_address), abi=ERC20_ABI)
        
        name = await token_contract.functions.name().call()
        symbol = await token_contract.functions.symbol().call()
        decimals = await token_contract.functions.decimals().call()
        total_supply = await token_contract.functions.totalSupply().call()
        
        formatted_supply = total_supply / (10 ** decimals)
        
        return ToolResult(content=[TextContent(text=f"### Token Metadata\n**Name**: {name}\n**Symbol**: {symbol}\n**Decimals**: {decimals}\n**Total Supply**: {formatted_supply:,.2f}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_token_allowance(arguments: dict) -> ToolResult:
    """
    Get Token Allowance (Owner -> Spender).
    """
    token_address = arguments.get("token_address")
    owner_address = arguments.get("owner_address")
    spender_address = arguments.get("spender_address")
    
    try:
        w3 = await get_web3_instance(arguments)
        token_contract = w3.eth.contract(address=w3.to_checksum_address(token_address), abi=ERC20_ABI)
        
        allowance = await token_contract.functions.allowance(w3.to_checksum_address(owner_address), w3.to_checksum_address(spender_address)).call()
        try:
             decimals = await token_contract.functions.decimals().call()
        except:
             decimals = 18

        fmt = allowance / (10 ** decimals)
        return ToolResult(content=[TextContent(text=f"### Allowance\n**Amount**: {fmt}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_token_total_supply(arguments: dict) -> ToolResult:
    """
    Get Token Total Supply.
    """
    token_address = arguments.get("token_address")
    try:
        w3 = await get_web3_instance(arguments)
        token_contract = w3.eth.contract(address=w3.to_checksum_address(token_address), abi=ERC20_ABI)
        supply = await token_contract.functions.totalSupply().call()
        try:
             decimals = await token_contract.functions.decimals().call()
        except:
             decimals = 18

        fmt = supply / (10 ** decimals)
        return ToolResult(content=[TextContent(text=f"{fmt:,.2f}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
