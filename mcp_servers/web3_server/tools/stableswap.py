
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.web3_server.tools.network import get_web3_instance

CURVE_3POOL_ADDRESS = "0xbebc44782986428c714c1a599724a8d0c87fe639"
# ABI for get_dy(i, j, dx)
CURVE_ABI = [{"stateMutability":"view","type":"function","name":"get_dy","inputs":[{"name":"i","type":"int128"},{"name":"j","type":"int128"},{"name":"dx","type":"uint256"}],"outputs":[{"name":"","type":"uint256"}]}]

# 0: DAI, 1: USDC, 2: USDT
COINS = {"DAI": 0, "USDC": 1, "USDT": 2}
DECIMALS = {"DAI": 18, "USDC": 6, "USDT": 6}

async def get_curve_quote(arguments: dict) -> ToolResult:
    """
    Get StableSwap Quote (Curve 3Pool).
    Supported: DAI, USDC, USDT.
    """
    token_in = arguments.get("token_in").upper()
    token_out = arguments.get("token_out").upper()
    amount_in = float(arguments.get("amount_in"))
    
    if token_in not in COINS or token_out not in COINS:
        return ToolResult(isError=True, content=[TextContent(text=f"Only DAI, USDC, USDT supported. Got {token_in}->{token_out}")])
        
    try:
        w3 = await get_web3_instance(arguments)
        pool = w3.eth.contract(address=CURVE_3POOL_ADDRESS, abi=CURVE_ABI)
        
        i = COINS[token_in]
        j = COINS[token_out]
        
        decimals_in = DECIMALS[token_in]
        amount_in_wei = int(amount_in * (10 ** decimals_in))
        
        amount_out_wei = await pool.functions.get_dy(i, j, amount_in_wei).call()
        
        decimals_out = DECIMALS[token_out]
        amount_out = amount_out_wei / (10 ** decimals_out)
        
        return ToolResult(content=[TextContent(text=f"### Curve Quote\n**In**: {amount_in} {token_in}\n**Out**: {amount_out} {token_out}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
