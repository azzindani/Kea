
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.web3_server.tools.network import get_web3_instance
from web3 import Web3

# Uniswap V3 Quoter (Mainnet, Optimism, Arbitrum, Polygon, etc. usually same address or deployment)
# Mainnet: 0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6
QUOTER_ADDRESS = "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6"

# Minimal ABI for quoteExactInputSingle
QUOTER_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "tokenIn", "type": "address"},
            {"internalType": "address", "name": "tokenOut", "type": "address"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"},
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
        ],
        "name": "quoteExactInputSingle",
        "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

async def get_uniswap_price(arguments: dict) -> ToolResult:
    """
    Get Token Price from Uniswap V3 Quoter.
    Default Fee: 3000 (0.3%).
    """
    token_in = arguments.get("token_in")
    token_out = arguments.get("token_out") # e.g. USDT/WETH
    amount_in = arguments.get("amount_in", 1.0)
    fee = int(arguments.get("fee", 3000))
    
    try:
        w3 = await get_web3_instance(arguments)
        quoter = w3.eth.contract(address=QUOTER_ADDRESS, abi=QUOTER_ABI)
        
        # Need decimals to convert amount_in to wei
        # We need a quick way to get decimals. For now assume user provides raw or we fetch?
        # Let's fetch decimals for token_in
        erc20_abi = [{"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]
        
        try:
             c_in = w3.eth.contract(address=w3.to_checksum_address(token_in), abi=erc20_abi)
             decimals_in = await c_in.functions.decimals().call()
        except:
             decimals_in = 18 
             
        amount_in_wei = int(float(amount_in) * (10 ** decimals_in))
        
        # Call Quoter
        amount_out_wei = await quoter.functions.quoteExactInputSingle(
            w3.to_checksum_address(token_in),
            w3.to_checksum_address(token_out),
            fee,
            amount_in_wei,
            0
        ).call()
        
        # Decimals out
        try:
             c_out = w3.eth.contract(address=w3.to_checksum_address(token_out), abi=erc20_abi)
             decimals_out = await c_out.functions.decimals().call()
        except:
             decimals_out = 18
             
        amount_out = amount_out_wei / (10 ** decimals_out)
        
        price = amount_out / float(amount_in)
        
        return ToolResult(content=[TextContent(text=f"### Uniswap V3 Price\n**In**: {amount_in} ({token_in})\n**Out**: {amount_out} ({token_out})\n**Rate**: 1 In = {price} Out")])
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=f"Uniswap Error: {str(e)}. (Note: Quoter address might differ on non-mainnet chains).")])
