
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)



from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.web3_server.tools import (
    rpc, erc20, erc721, multicall, ens, utils, network,
    staking, stableswap, security, contract_interaction, identity, weth,
    lending, oracle, defi, events, action, wallet, gas
)
import structlog
import asyncio

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging(force_stderr=True)

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
    """RETRIEVES block details. [ACTION]
    
    [RAG Context]
    Queries the blockchain for information about a specific block. Blocks are the fundamental units of the chain, containing groups of transactions.
    
    How to Use:
    - 'block_id': Can be a number (hex or int), a hash (0x...), or tags like 'latest', 'earliest', 'pending'.
    - Use 'full_transactions=True' to get the details of every transaction inside the block (Heavy).
    
    Keywords: block header, miner info, timestamp, block explorer.
    """
    return await run_op(rpc.get_block, block_id=block_id, full_transactions=full_transactions, rpc_url=rpc_url)

@mcp.tool()
async def get_transaction(tx_hash: str, rpc_url: str = None) -> str:
    """RETRIEVES transaction details. [ACTION]
    
    [RAG Context]
    Returns sender, receiver, value, gas used, and status.
    Args:
        tx_hash: 0x... hash string.
    """
    return await run_op(rpc.get_transaction, tx_hash=tx_hash, rpc_url=rpc_url)

@mcp.tool()
async def get_balance(address: str, block_id: str = "latest", rpc_url: str = None) -> str:
    """FETCHES ETH balance. [ACTION]
    
    [RAG Context]
    Retrieves the native Ether (ETH) balance of any Ethereum address.
    
    How to Use:
    - Returns the balance in 'Wei' (the smallest unit of ETH). 1 ETH = 10^18 Wei.
    - Use the 'from_wei' tool to convert this into a human-readable Ether value.
    
    Keywords: wallet funds, eth balance, native currency, account wealth.
    """
    return await run_op(rpc.get_balance, address=address, block_id=block_id, rpc_url=rpc_url)

@mcp.tool()
async def get_gas_price(rpc_url: str = None) -> str:
    """FETCHES gas prices. [ACTION]
    
    [RAG Context]
    Retrieves the current network fee required to process a transaction. Gas prices fluctuate based on network congestion.
    
    How to Use:
    - Crucial for estimating if a transaction will be accepted by miners/validators.
    - High gas price means high demand; you may want to wait for lower fees before sending large trades.
    
    Keywords: transaction fees, network cost, gwei, priority fee.
    """
    return await run_op(rpc.get_gas_price, rpc_url=rpc_url)

@mcp.tool()
async def get_block_number(rpc_url: str = None) -> str:
    """FETCHES current block number. [ACTION]
    
    [RAG Context]
    Retrieves the index of the most recent block successfully added to the blockchain. This serves as the system's "heartbeat" and is used to measure the passage of time or the confirmation depth of recent transactions.
    
    How to Use:
    - Useful for determining if the network is stalled or if your local RPC node is synchronized.
    - Used as a reference point for 'from_block' and 'to_block' in event indexing.
    
    Keywords: block height, current block, chain status, network sync.
    """
    return await run_op(rpc.get_block_number, rpc_url=rpc_url)

@mcp.tool()
async def get_transaction_count(address: str, rpc_url: str = None) -> str:
    """FETCHES transaction count (Nonce). [ACTION]
    
    [RAG Context]
    Retrieves the 'nonce' of an Ethereum address, which represents the number of transactions sent from that account. Every transaction sent MUST have a nonce exactly one higher than the previous one.
    
    How to Use:
    - Critical for transaction construction; if you use the wrong nonce, the transaction will be rejected by the network.
    - Also used to identify if an account has any outgoing history.
    
    Keywords: account nonce, tx sequence, transaction indexing, sender statistics.
    """
    return await run_op(rpc.get_transaction_count, address=address, rpc_url=rpc_url)

@mcp.tool()
async def get_chain_id(rpc_url: str = None) -> str:
    """FETCHES Chain ID. [ACTION]
    
    [RAG Context]
    Identifies the specific blockchain network being queried. This is a security feature that prevents a transaction from being "replayed" on another chain (e.g., a transaction meant for a testnet being valid on Mainnet).
    
    How to Use:
    - 1: Ethereum Mainnet
    - 137: Polygon
    - 42161: Arbitrum
    - 10: Optimism
    - 8453: Base
    
    Keywords: network id, chain identifier, eip-155, replay protection.
    """
    return await run_op(rpc.get_chain_id, rpc_url=rpc_url)

@mcp.tool()
async def get_code(address: str, rpc_url: str = None) -> str:
    """FETCHES contract bytecode. [ACTION]
    
    [RAG Context]
    Returns "0x" if address is an EOA (User Wallet).
    Returns bytecode if address is a Contract.
    """
    return await run_op(rpc.get_code, address=address, rpc_url=rpc_url)

@mcp.tool()
async def switch_chain(chain: str) -> str:
    """SWITCHES default network. [ACTION]
    
    [RAG Context]
    Changes the active network context for all subsequent Web3 calls.
    
    How to Use:
    - Supported: 'ethereum' (Mainnet), 'arbitrum', 'optimism', 'polygon', 'bsc', 'base'.
    - CRITICAL: You MUST call this first if you intend to interact with Layer 2s or sidechains.
    
    Keywords: change network, l2 switch, polygon rpc, arbitrum rpc, base chain.
    """
    return await run_op(network.switch_chain, chain=chain)

# 2. MARKETS (ERC20/721)
@mcp.tool()
async def get_token_balance(token_address: str, wallet_address: str, rpc_url: str = None) -> str:
    """FETCHES ERC20 token balance. [ACTION]
    
    [RAG Context]
    Queries an ERC20 smart contract (like USDT, USDC, LINK) to find how much of that specific token is held by a wallet address.
    
    How to Use:
    - Input the token contract address and the user's wallet address.
    
    Keywords: erc20 balance, asset holdings, digital assets, token tracker.
    """
    return await run_op(erc20.get_token_balance, token_address=token_address, wallet_address=wallet_address, rpc_url=rpc_url)

@mcp.tool()
async def get_token_metadata(token_address: str, rpc_url: str = None) -> str:
    """FETCHES ERC20 metadata. [ACTION]
    
    [RAG Context]
    Use to verify if a contract address is actually the token you think it is.
    """
    return await run_op(erc20.get_token_metadata, token_address=token_address, rpc_url=rpc_url)

@mcp.tool()
async def get_token_allowance(token_address: str, owner_address: str, spender_address: str) -> str:
    """FETCHES token allowance. [ACTION]
    
    [RAG Context]
    Checks ERC20 approval status.
    """
    return await run_op(erc20.get_token_allowance, token_address=token_address, owner_address=owner_address, spender_address=spender_address)

@mcp.tool()
async def get_token_total_supply(token_address: str) -> str:
    """FETCHES token total supply. [ACTION]
    
    [RAG Context]
    """
    return await run_op(erc20.get_token_total_supply, token_address=token_address)

@mcp.tool()
async def get_nft_owner(token_address: str, token_id: str, rpc_url: str = None) -> str:
    """FETCHES NFT owner. [ACTION]
    
    [RAG Context]
    Returns 0x address of the current owner.
    """
    return await run_op(erc721.get_nft_owner, token_address=token_address, token_id=token_id, rpc_url=rpc_url)

@mcp.tool()
async def get_nft_metadata_uri(token_address: str, token_id: str, rpc_url: str = None) -> str:
    """FETCHES NFT Metadata URI. [ACTION]
    
    [RAG Context]
    Target URL often contains the JSON metadata (image, attributes).
    """
    return await run_op(erc721.get_nft_metadata_uri, token_address=token_address, token_id=token_id, rpc_url=rpc_url)

# 3. MULTICALL (BULK)
@mcp.tool()
async def get_bulk_balances(addresses: list[str], rpc_url: str = None) -> str:
    """FETCHES ETH balances for multiple addresses. [ACTION]
    
    [RAG Context]
    Efficient batch retrieval.
    """
    return await run_op(multicall.get_bulk_balances, addresses=addresses, rpc_url=rpc_url)

@mcp.tool()
async def get_bulk_token_balances(wallet_address: str, token_addresses: list[str], rpc_url: str = None) -> str:
    """FETCHES multiple token balances. [ACTION]
    
    [RAG Context]
    Args:
        wallet_address: User to check
        token_addresses: List of ERC20 contract addresses
    """
    return await run_op(multicall.get_bulk_token_balances, wallet_address=wallet_address, token_addresses=token_addresses, rpc_url=rpc_url)

# 4. UTILS/ENS
@mcp.tool()
async def resolve_ens(name: str, rpc_url: str = None) -> str:
    """RESOLVES ENS name. [ACTION]
    
    [RAG Context]
    Example:
    - resolve_ens("vitalik.eth") -> "0xd8dA6BF..."
    """
    return await run_op(ens.resolve_ens, name=name, rpc_url=rpc_url)

@mcp.tool()
async def to_wei(amount: float, unit: str) -> str:
    """CONVERTS to Wei. [ACTION]
    
    [RAG Context]
    Example: to_wei(1.5, "ether")
    """
    return await run_op(utils.to_wei, amount=amount, unit=unit)

@mcp.tool()
async def from_wei(amount: float, unit: str) -> str:
    """CONVERTS from Wei. [ACTION]
    
    [RAG Context]
    Example: from_wei(1000000000000000000, "ether") -> "1.0"
    """
    return await run_op(utils.from_wei, amount=amount, unit=unit)

# 6. PHASE 3: DEFI, EVENTS, ACTION
@mcp.tool()
async def get_uniswap_price(token_in: str, token_out: str, amount_in: float, fee: int, rpc_url: str = None) -> str:
    """FETCHES Uniswap V3 price quote. [ACTION]
    
    [RAG Context]
    Queries the Uniswap V3 Quoter contract to find the expected output for a swap between two tokens. This is the on-chain "Market Price".
    
    How to Use:
    - 'fee': Common V3 fee tiers are 500 (0.05%), 3000 (0.3%), or 10000 (1%). 
    - Essential for calculating swap efficiency and potential slippage.
    
    Keywords: coin price, swap quote, uniswap trade, on-chain market.
    """
    return await run_op(defi.get_uniswap_price, token_in=token_in, token_out=token_out, amount_in=amount_in, fee=fee, rpc_url=rpc_url)

@mcp.tool()
async def get_contract_events(address: str, from_block: str, topics: list, rpc_url: str = None) -> str:
    """SEARCHES contract events. [ACTION]
    
    [RAG Context]
    Advanced tool for indexing historical activity.
    """
    return await run_op(events.get_contract_events, address=address, from_block=from_block, topics=topics, rpc_url=rpc_url)

@mcp.tool()
async def send_eth(to_address: str, amount: float, private_key: str, rpc_url: str = None) -> str:
    """SENDS native ETH. [ACTION]
    
    [RAG Context]
    Constructs, signs, and broadcasts a Transfer transaction for native Ether (ETH).
    
    CAUTION: 
    - This is a non-reversible execution. 
    - Requires the 'private_key' of the sender. 
    - Ensure 'amount' is in ETH (not Wei).
    
    Keywords: transfer funds, send crypto, eth payment, blockchain tx.
    """
    return await run_op(action.send_eth, to_address=to_address, amount=amount, private_key=private_key, rpc_url=rpc_url)

@mcp.tool()
async def approve_token(token_address: str, spender_address: str, amount: float, private_key: str, rpc_url: str = None) -> str:
    """APPROVES token spender. [ACTION]
    
    [RAG Context]
    Standard ERC20 'approve' call.
    """
    return await run_op(action.approve_token, token_address=token_address, spender_address=spender_address, amount=amount, private_key=private_key, rpc_url=rpc_url)

@mcp.tool()
async def generate_wallet() -> str:
    """CREATES new wallet. [ACTION]
    
    [RAG Context]
    Returns Address and Private Key.
    SECURITY WARNING: Keys are generated locally.
    """
    return await run_op(wallet.generate_wallet)

@mcp.tool()
async def estimate_gas(to_address: str, data: str, value: float, rpc_url: str = None) -> str:
    """ESTIMATES gas units. [ACTION]
    
    [RAG Context]
    Use before sending to prevent out-of-gas errors.
    """
    return await run_op(gas.estimate_gas, to_address=to_address, data=data, value=value, rpc_url=rpc_url)

# 7. PHASE 4: LENDING & ORACLES
@mcp.tool()
async def get_aave_reserve_data(asset: str, rpc_url: str = None) -> str:
    """FETCHES Aave V3 reserve data. [ACTION]
    
    [RAG Context]
    Queries the Aave lending protocol for liquidity and yield data on a specific asset.
    
    How to Use:
    - Returns 'Supply APY' (what you earn for lending) and 'Borrow APY' (what you pay to borrow).
    - Checks for protocol liquidity to ensure you can withdraw assets.
    
    Keywords: lending rates, yield farming, aave yield, borrow apy.
    """
    return await run_op(lending.get_aave_reserve_data, asset=asset, rpc_url=rpc_url)

@mcp.tool()
async def get_aave_user_account_data(user_address: str, rpc_url: str = None) -> str:
    """FETCHES Aave user data. [ACTION]
    
    [RAG Context]
    Checks if a user is close to liquidation.
    """
    return await run_op(lending.get_aave_user_account_data, user_address=user_address, rpc_url=rpc_url)

@mcp.tool()
async def get_chainlink_price(feed_address: str, rpc_url: str = None) -> str:
    """FETCHES Chainlink price. [ACTION]
    
    [RAG Context]
    Most reliable source for on-chain asset prices.
    """
    return await run_op(oracle.get_chainlink_price, feed_address=feed_address, rpc_url=rpc_url)

# 8. PHASE 5: UNIVERSAL & IDENTITY
@mcp.tool()
async def read_contract(address: str, function_signature: str, args: list, arg_types: list, return_types: list, rpc_url: str = None) -> str:
    """CALLS contract function (Read). [ACTION]
    
    [RAG Context]
    A powerful, low-level tool that allows reading data from ANY smart contract on the blockchain without needing the full ABI.
    
    How to Use:
    - Provide the 'function_signature' (e.g., "balanceOf(address)").
    - Map 'args' to 'arg_types' (e.g., ["0x..."], ["address"]).
    - Identify 'return_types' (e.g., ["uint256"]).
    
    Keywords: generic contract, low-level call, state query, smart contract data.
    """
    return await run_op(contract_interaction.read_contract, address=address, function_signature=function_signature, args=args, arg_types=arg_types, return_types=return_types, rpc_url=rpc_url)

@mcp.tool()
async def decode_transaction(tx_hash: str, abi: str, rpc_url: str = None) -> str:
    """DECODES transaction data. [ACTION]
    
    [RAG Context]
    """
    return await run_op(contract_interaction.decode_transaction, tx_hash=tx_hash, abi=abi, rpc_url=rpc_url)

@mcp.tool()
async def get_ens_reverse_record(address: str, rpc_url: str = None) -> str:
    """RESOLVES address to ENS. [ACTION]
    
    [RAG Context]
    Reverse lookup.
    """
    return await run_op(identity.get_ens_reverse_record, address=address, rpc_url=rpc_url)

@mcp.tool()
async def wrap_eth(amount: float, private_key: str, rpc_url: str = None) -> str:
    """WRAPS ETH to WETH. [ACTION]
    
    [RAG Context]
    Mints WETH 1:1.
    """
    return await run_op(weth.wrap_eth, amount=amount, private_key=private_key, rpc_url=rpc_url)

@mcp.tool()
async def unwrap_eth(amount: float, private_key: str, rpc_url: str = None) -> str:
    """UNWRAPS WETH to ETH. [ACTION]
    
    [RAG Context]
    Burns WETH.
    """
    return await run_op(weth.unwrap_eth, amount=amount, private_key=private_key, rpc_url=rpc_url)

# 9. PHASE 6: YIELD & SAFETY
@mcp.tool()
async def stake_eth_lido(amount: float, private_key: str, rpc_url: str = None) -> str:
    """STAKES ETH (Lido). [ACTION]
    
    [RAG Context]
    Liquid staking.
    """
    return await run_op(staking.stake_eth_lido, amount=amount, private_key=private_key, rpc_url=rpc_url)

@mcp.tool()
async def get_curve_quote(token_in: str, token_out: str, amount_in: float, rpc_url: str = None) -> str:
    """FETCHES Curve swap quote. [ACTION]
    
    [RAG Context]
    Best for stablecoin swaps.
    """
    return await run_op(stableswap.get_curve_quote, token_in=token_in, token_out=token_out, amount_in=amount_in, rpc_url=rpc_url)

@mcp.tool()
async def simulate_transaction(to_address: str, value: float, data: str, from_address: str, rpc_url: str = None) -> str:
    """SIMULATES transaction. [ACTION]
    
    [RAG Context]
    Executes a transaction in a local, virtualized state to determine its outcome without actually broadcasting it to the blockchain (Dry Run).
    
    How to Use:
    - CRITICAL for security. Use this to check for potential errors, reverted transactions, or malicious contract outcomes before risking real funds.
    
    Keywords: dry run, trace transaction, security audit, gas check outcome.
    """
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
    """FETCHES ETH/USD price. [ACTION]
    
    [RAG Context]
    A high-precision "Super Tool" for fetching the definitive ETH/USD exchange rate. It queries the Chainlink decentralized oracle network, which aggregates prices from dozens of high-volume exchanges.
    
    How to Use:
    - Returns the current price of Ethereum in US Dollars. 
    - Essential for calculating the fiat value of gas fees, portfolio holdings, or DeFi liquidation thresholds.
    
    Keywords: eth price, ethereum value, chainlink oracle, market rate.
    """
    return await run_op(oracle.get_chainlink_price, feed_address="0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419")

@mcp.tool()
async def get_chainlink_btc_usd() -> str:
    """FETCHES BTC/USD price. [ACTION]
    
    [RAG Context]
    A critical "Super Tool" for Bitcoin pricing on-chain. It utilizes the Chainlink network to provide the highly accurate BTC/USD benchmark price used by major DeFi platforms for collateral valuation.
    
    How to Use:
    - Useful for cross-asset analysis or when calculating the BTC-equivalent value of an Ethereum-based portfolio.
    
    Keywords: bitcoin price, btc value, crypto oracle, btc market.
    """
    return await run_op(oracle.get_chainlink_price, feed_address="0xF4030086522a5bEEa4988F8cA5B36dbC97BeE88c")

@mcp.tool()
async def get_chainlink_usdc_usd() -> str:
    """FETCHES USDC/USD price. [ACTION]
    
    [RAG Context]
    A stability-monitoring "Super Tool". While USDC is a stablecoin pegged to 1 USD, its on-chain price can fluctuate slightly during market stress. This oracle provides the real-time market value.
    
    How to Use:
    - Essential for verifying that a stablecoin has not "depegged" before using it as collateral in a loan.
    
    Keywords: usdc peg, stablecoin price, dollar parity, liquidity check.
    """
    return await run_op(oracle.get_chainlink_price, feed_address="0x8fFfFfd4AfB6115b954Bd326cbe7B4BA576818f6")

# Register dynamic shortcuts
for sym, addr in tokens.items():
    # Balance
    def make_bal_handler(a=addr):
        async def handler(wallet_address: str):
            return await run_op(erc20.get_token_balance, token_address=a, wallet_address=wallet_address)
        return handler
    
    mcp.add_tool(
        name=f"get_{sym}_balance",
        description=f"SHORTCUT: Get {sym.upper()} Balance.",
        fn=make_bal_handler()
    )

    # Price
    def make_price_handler(a=addr):
        async def handler():
            return await run_op(defi.get_uniswap_price, token_in=a, token_out="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", amount_in=1.0, fee=3000)
        return handler

    mcp.add_tool(
        name=f"get_{sym}_price",
        description=f"SHORTCUT: Get {sym.upper()} Price (in USDC).",
        fn=make_price_handler()
    )

    # Aave
    def make_aave_handler(a=addr):
        async def handler():
            return await run_op(lending.get_aave_reserve_data, asset=a)
        return handler

    mcp.add_tool(
        name=f"get_{sym}_aave_data",
        description=f"SHORTCUT: Get {sym.upper()} Aave Rates.",
        fn=make_aave_handler()
    )

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class Web3Server:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []

