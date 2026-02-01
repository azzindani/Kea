
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)



from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from tools import (
    rpc, erc20, erc721, multicall, ens, utils, network,
    staking, stableswap, security, contract_interaction, identity, weth,
    lending, oracle, defi, events, action, wallet, gas
)
import structlog
import asyncio

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("web3_server", dependencies=["web3"])

async def run_op(op_func, diff_args=None, **kwargs):
    """
    Helper to run legacy tool ops.
    diff_args: dict of overrides/additions to kwargs before passing to op.
    """
    try:
        # Combine args
        final_args = kwargs.copy()
        if diff_args:
            final_args.update(diff_args)
            
        # The tools expect a single 'arguments' dict.
        result = await op_func(final_args)
        
        # Unwrap ToolResult
        if hasattr(result, 'content') and result.content:
            text_content = ""
            for item in result.content:
                if hasattr(item, 'text'):
                    text_content += item.text + "\n"
            return text_content.strip()
        
        if hasattr(result, 'isError') and result.isError:
            return "Error: Tool returned error status."
            
        return str(result)
    except Exception as e:
        return f"Error executing tool: {e}"

# 1. CORE RPC
@mcp.tool()
async def get_block(block_id: str = "latest", full_transactions: bool = False, rpc_url: str = None) -> str:
    """RPC: Get Block Info (Hash/Number)."""
    return await run_op(rpc.get_block, block_id=block_id, full_transactions=full_transactions, rpc_url=rpc_url)

@mcp.tool()
async def get_transaction(tx_hash: str, rpc_url: str = None) -> str:
    """RPC: Get Tx Details."""
    return await run_op(rpc.get_transaction, tx_hash=tx_hash, rpc_url=rpc_url)

@mcp.tool()
async def get_balance(address: str, block_id: str = "latest", rpc_url: str = None) -> str:
    """RPC: Get Native Balance."""
    return await run_op(rpc.get_balance, address=address, block_id=block_id, rpc_url=rpc_url)

@mcp.tool()
async def get_gas_price(rpc_url: str = None) -> str:
    """RPC: Get Gas Prices."""
    return await run_op(rpc.get_gas_price, rpc_url=rpc_url)

@mcp.tool()
async def get_block_number(rpc_url: str = None) -> str:
    """RPC: Get Current Height."""
    return await run_op(rpc.get_block_number, rpc_url=rpc_url)

@mcp.tool()
async def get_transaction_count(address: str, rpc_url: str = None) -> str:
    """RPC: Get Nonce."""
    return await run_op(rpc.get_transaction_count, address=address, rpc_url=rpc_url)

@mcp.tool()
async def get_chain_id(rpc_url: str = None) -> str:
    """RPC: Get Chain ID."""
    return await run_op(rpc.get_chain_id, rpc_url=rpc_url)

@mcp.tool()
async def get_code(address: str, rpc_url: str = None) -> str:
    """RPC: Get Contract Code."""
    return await run_op(rpc.get_code, address=address, rpc_url=rpc_url)

@mcp.tool()
async def switch_chain(chain: str) -> str:
    """NET: Switch Default Chain (ethereum, arbitrum, optimism, polygon, bsc, base)."""
    return await run_op(network.switch_chain, chain=chain)

# 2. MARKETS (ERC20/721)
@mcp.tool()
async def get_token_balance(token_address: str, wallet_address: str, rpc_url: str = None) -> str:
    """ERC20: Get Token Balance."""
    return await run_op(erc20.get_token_balance, token_address=token_address, wallet_address=wallet_address, rpc_url=rpc_url)

@mcp.tool()
async def get_token_metadata(token_address: str, rpc_url: str = None) -> str:
    """ERC20: Get Metadata."""
    return await run_op(erc20.get_token_metadata, token_address=token_address, rpc_url=rpc_url)

@mcp.tool()
async def get_token_allowance(token_address: str, owner_address: str, spender_address: str) -> str:
    """ERC20: Get Allowance."""
    return await run_op(erc20.get_token_allowance, token_address=token_address, owner_address=owner_address, spender_address=spender_address)

@mcp.tool()
async def get_token_total_supply(token_address: str) -> str:
    """ERC20: Get Total Supply."""
    return await run_op(erc20.get_token_total_supply, token_address=token_address)

@mcp.tool()
async def get_nft_owner(token_address: str, token_id: str, rpc_url: str = None) -> str:
    """ERC721: Get Owner."""
    return await run_op(erc721.get_nft_owner, token_address=token_address, token_id=token_id, rpc_url=rpc_url)

@mcp.tool()
async def get_nft_metadata_uri(token_address: str, token_id: str, rpc_url: str = None) -> str:
    """ERC721: Get Metadata URI."""
    return await run_op(erc721.get_nft_metadata_uri, token_address=token_address, token_id=token_id, rpc_url=rpc_url)

# 3. MULTICALL (BULK)
@mcp.tool()
async def get_bulk_balances(addresses: list[str], rpc_url: str = None) -> str:
    """MULTICALL: Get ETH Balances for Multiple Addresses."""
    return await run_op(multicall.get_bulk_balances, addresses=addresses, rpc_url=rpc_url)

@mcp.tool()
async def get_bulk_token_balances(wallet_address: str, token_addresses: list[str], rpc_url: str = None) -> str:
    """MULTICALL: Get Balances for 1 Wallet across Tokens."""
    return await run_op(multicall.get_bulk_token_balances, wallet_address=wallet_address, token_addresses=token_addresses, rpc_url=rpc_url)

# 4. UTILS/ENS
@mcp.tool()
async def resolve_ens(name: str, rpc_url: str = None) -> str:
    """ENS: Resolve Name (Mainnet)."""
    return await run_op(ens.resolve_ens, name=name, rpc_url=rpc_url)

@mcp.tool()
async def to_wei(amount: float, unit: str) -> str:
    """UTIL: Convert to Wei."""
    return await run_op(utils.to_wei, amount=amount, unit=unit)

@mcp.tool()
async def from_wei(amount: float, unit: str) -> str:
    """UTIL: Convert from Wei."""
    return await run_op(utils.from_wei, amount=amount, unit=unit)

# 6. PHASE 3: DEFI, EVENTS, ACTION
@mcp.tool()
async def get_uniswap_price(token_in: str, token_out: str, amount_in: float, fee: int, rpc_url: str = None) -> str:
    """DEFI: Get Token Price (Uniswap V3)."""
    return await run_op(defi.get_uniswap_price, token_in=token_in, token_out=token_out, amount_in=amount_in, fee=fee, rpc_url=rpc_url)

@mcp.tool()
async def get_contract_events(address: str, from_block: str, topics: list, rpc_url: str = None) -> str:
    """EVENTS: Get Contract Logs."""
    return await run_op(events.get_contract_events, address=address, from_block=from_block, topics=topics, rpc_url=rpc_url)

@mcp.tool()
async def send_eth(to_address: str, amount: float, private_key: str, rpc_url: str = None) -> str:
    """ACTION: Send ETH (Native)."""
    return await run_op(action.send_eth, to_address=to_address, amount=amount, private_key=private_key, rpc_url=rpc_url)

@mcp.tool()
async def approve_token(token_address: str, spender_address: str, amount: float, private_key: str, rpc_url: str = None) -> str:
    """ACTION: Approve Token Spender."""
    return await run_op(action.approve_token, token_address=token_address, spender_address=spender_address, amount=amount, private_key=private_key, rpc_url=rpc_url)

@mcp.tool()
async def generate_wallet() -> str:
    """WALLET: Generate New Wallet."""
    return await run_op(wallet.generate_wallet)

@mcp.tool()
async def estimate_gas(to_address: str, data: str, value: float, rpc_url: str = None) -> str:
    """GAS: Estimate Transaction Gas."""
    return await run_op(gas.estimate_gas, to_address=to_address, data=data, value=value, rpc_url=rpc_url)

# 7. PHASE 4: LENDING & ORACLES
@mcp.tool()
async def get_aave_reserve_data(asset: str, rpc_url: str = None) -> str:
    """LENDING: Aave V3 APY Data."""
    return await run_op(lending.get_aave_reserve_data, asset=asset, rpc_url=rpc_url)

@mcp.tool()
async def get_aave_user_account_data(user_address: str, rpc_url: str = None) -> str:
    """LENDING: Aave User Health."""
    return await run_op(lending.get_aave_user_account_data, user_address=user_address, rpc_url=rpc_url)

@mcp.tool()
async def get_chainlink_price(feed_address: str, rpc_url: str = None) -> str:
    """ORACLE: Chainlink Feed Price."""
    return await run_op(oracle.get_chainlink_price, feed_address=feed_address, rpc_url=rpc_url)

# 8. PHASE 5: UNIVERSAL & IDENTITY
@mcp.tool()
async def read_contract(address: str, function_signature: str, args: list, arg_types: list, return_types: list, rpc_url: str = None) -> str:
    """UNIVERSAL: Call Any Contract View Function."""
    return await run_op(contract_interaction.read_contract, address=address, function_signature=function_signature, args=args, arg_types=arg_types, return_types=return_types, rpc_url=rpc_url)

@mcp.tool()
async def decode_transaction(tx_hash: str, abi: str, rpc_url: str = None) -> str:
    """UNIVERSAL: Decode Input Data."""
    return await run_op(contract_interaction.decode_transaction, tx_hash=tx_hash, abi=abi, rpc_url=rpc_url)

@mcp.tool()
async def get_ens_reverse_record(address: str, rpc_url: str = None) -> str:
    """IDENTITY: Address to Name."""
    return await run_op(identity.get_ens_reverse_record, address=address, rpc_url=rpc_url)

@mcp.tool()
async def wrap_eth(amount: float, private_key: str, rpc_url: str = None) -> str:
    """WETH: Wrap ETH."""
    return await run_op(weth.wrap_eth, amount=amount, private_key=private_key, rpc_url=rpc_url)

@mcp.tool()
async def unwrap_eth(amount: float, private_key: str, rpc_url: str = None) -> str:
    """WETH: Unwrap WETH."""
    return await run_op(weth.unwrap_eth, amount=amount, private_key=private_key, rpc_url=rpc_url)

# 9. PHASE 6: YIELD & SAFETY
@mcp.tool()
async def stake_eth_lido(amount: float, private_key: str, rpc_url: str = None) -> str:
    """YIELD: Stake ETH on Lido."""
    return await run_op(staking.stake_eth_lido, amount=amount, private_key=private_key, rpc_url=rpc_url)

@mcp.tool()
async def get_curve_quote(token_in: str, token_out: str, amount_in: float, rpc_url: str = None) -> str:
    """YIELD: Curve Stable Quote."""
    return await run_op(stableswap.get_curve_quote, token_in=token_in, token_out=token_out, amount_in=amount_in, rpc_url=rpc_url)

@mcp.tool()
async def simulate_transaction(to_address: str, value: float, data: str, from_address: str, rpc_url: str = None) -> str:
    """SAFETY: Simulate Tx (Dry Run)."""
    return await run_op(security.simulate_transaction, to_address=to_address, value=value, data=data, from_address=from_address, rpc_url=rpc_url)

# --- DYNAMIC TOKEN SHORTCUTS ---
tokens = {
    "usdt": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "usdc": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "weth": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "dai": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    "shib": "0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE",
    "pepe": "0x6982508145454Ce325dDbE47a25d4ec3d2311933",
    "wbtc": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    "link": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
    "uni": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
    "matic": "0x7D1AfA7B718fb893dB30A3aBc0Cfc608AaCfeBB0",
    "steth": "0xae7ab96520DE3A18E5e111B5Ee5B82061ce70310",
    "fet": "0xaea46A60368A7bD060eec7DF8CBa43b7EF41Ad85",
    "rndr": "0x6De037ef9aD2725EB404906F1CC53138EA7Fb6E5",
    "aave": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"
}

# Chainlink Shortcuts
@mcp.tool()
async def get_chainlink_eth_usd() -> str:
    """SHORTCUT: Chainlink ETH/USD."""
    return await run_op(oracle.get_chainlink_price, feed_address="0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419")

@mcp.tool()
async def get_chainlink_btc_usd() -> str:
    """SHORTCUT: Chainlink BTC/USD."""
    return await run_op(oracle.get_chainlink_price, feed_address="0xF4030086522a5bEEa4988F8cA5B36dbC97BeE88c")

@mcp.tool()
async def get_chainlink_usdc_usd() -> str:
    """SHORTCUT: Chainlink USDC/USD."""
    return await run_op(oracle.get_chainlink_price, feed_address="0x8fFfFfd4AfB6115b954Bd326cbe7B4BA576818f6")

# Register dynamic shortcuts
for sym, addr in tokens.items():
    # Balance
    async def make_bal_handler(a=addr):
        async def handler(wallet_address: str):
            return await run_op(erc20.get_token_balance, token_address=a, wallet_address=wallet_address)
        return handler
    
    mcp.tool(name=f"get_{sym}_balance", description=f"SHORTCUT: Get {sym.upper()} Balance.")(
        make_bal_handler()
    )

    # Price
    async def make_price_handler(a=addr):
        async def handler():
            return await run_op(defi.get_uniswap_price, token_in=a, token_out="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", amount_in=1.0, fee=3000)
        return handler

    mcp.tool(name=f"get_{sym}_price", description=f"SHORTCUT: Get {sym.upper()} Price (in USDC).")(
        make_price_handler()
    )

    # Aave
    async def make_aave_handler(a=addr):
        async def handler():
            return await run_op(lending.get_aave_reserve_data, asset=a)
        return handler

    mcp.tool(name=f"get_{sym}_aave_data", description=f"SHORTCUT: Get {sym.upper()} Aave Rates.")(
        make_aave_handler()
    )

if __name__ == "__main__":
    mcp.run()