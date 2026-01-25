
from shared.mcp.server_base import MCPServer
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger

# Import Tools
from mcp_servers.web3_server.tools.rpc import get_block, get_transaction, get_balance, get_gas_price, get_block_number, get_transaction_count, get_chain_id, get_code
from mcp_servers.web3_server.tools.erc20 import get_token_balance, get_token_metadata, get_token_allowance, get_token_total_supply
from mcp_servers.web3_server.tools.erc721 import get_nft_owner, get_nft_metadata_uri
from mcp_servers.web3_server.tools.multicall import get_bulk_balances, get_bulk_token_balances
from mcp_servers.web3_server.tools.ens import resolve_ens
from mcp_servers.web3_server.tools.utils import to_wei, from_wei
from mcp_servers.web3_server.tools.network import switch_chain

class Web3Server(MCPServer):
    def __init__(self):
        super().__init__(name="web3_server", version="1.0.0")
        self.logger = get_logger(__name__)
        self._register_tools()

    def _register_tools(self):
        # 1. CORE RPC
        self.register_tool(name="get_block", description="RPC: Get Block Info (Hash/Number).", handler=get_block, parameters={"block_id": {"type": "string"}, "full_transactions": {"type": "boolean"}, "rpc_url": {"type": "string"}})
        self.register_tool(name="get_transaction", description="RPC: Get Tx Details.", handler=get_transaction, parameters={"tx_hash": {"type": "string"}, "rpc_url": {"type": "string"}})
        self.register_tool(name="get_balance", description="RPC: Get Native Balance.", handler=get_balance, parameters={"address": {"type": "string"}, "block_id": {"type": "string"}, "rpc_url": {"type": "string"}})
        self.register_tool(name="get_gas_price", description="RPC: Get Gas Prices.", handler=get_gas_price, parameters={"rpc_url": {"type": "string"}})
        self.register_tool(name="get_block_number", description="RPC: Get Current Height.", handler=get_block_number, parameters={"rpc_url": {"type": "string"}})
        self.register_tool(name="get_transaction_count", description="RPC: Get Nonce.", handler=get_transaction_count, parameters={"address": {"type": "string"}, "rpc_url": {"type": "string"}})
        self.register_tool(name="get_chain_id", description="RPC: Get Chain ID.", handler=get_chain_id, parameters={"rpc_url": {"type": "string"}})
        self.register_tool(name="get_code", description="RPC: Get Contract Code.", handler=get_code, parameters={"address": {"type": "string"}, "rpc_url": {"type": "string"}})
        self.register_tool(name="switch_chain", description="NET: Switch Default Chain (ethereum, arbitrum, optimism, polygon, bsc, base).", handler=switch_chain, parameters={"chain": {"type": "string"}})
        
        # 2. MARKETS (ERC20/721)
        self.register_tool(name="get_token_balance", description="ERC20: Get Token Balance.", handler=get_token_balance, parameters={"token_address": {"type": "string"}, "wallet_address": {"type": "string"}, "rpc_url": {"type": "string"}})
        self.register_tool(name="get_token_metadata", description="ERC20: Get Metadata.", handler=get_token_metadata, parameters={"token_address": {"type": "string"}, "rpc_url": {"type": "string"}})
        self.register_tool(name="get_token_allowance", description="ERC20: Get Allowance.", handler=get_token_allowance, parameters={"token_address": {"type": "string"}, "owner_address": {"type": "string"}, "spender_address": {"type": "string"}})
        self.register_tool(name="get_token_total_supply", description="ERC20: Get Total Supply.", handler=get_token_total_supply, parameters={"token_address": {"type": "string"}})
        
        self.register_tool(name="get_nft_owner", description="ERC721: Get Owner.", handler=get_nft_owner, parameters={"token_address": {"type": "string"}, "token_id": {"type": "string"}, "rpc_url": {"type": "string"}})
        self.register_tool(name="get_nft_metadata_uri", description="ERC721: Get Metadata URI.", handler=get_nft_metadata_uri, parameters={"token_address": {"type": "string"}, "token_id": {"type": "string"}, "rpc_url": {"type": "string"}})
        
        # 3. MULTICALL (BULK)
        self.register_tool(name="get_bulk_balances", description="MULTICALL: Get ETH Balances for Multiple Addresses.", handler=get_bulk_balances, parameters={"addresses": {"type": "array", "items": {"type": "string"}}, "rpc_url": {"type": "string"}})
        self.register_tool(name="get_bulk_token_balances", description="MULTICALL: Get Balances for 1 Wallet across Tokens.", handler=get_bulk_token_balances, parameters={"wallet_address": {"type": "string"}, "token_addresses": {"type": "array", "items": {"type": "string"}}, "rpc_url": {"type": "string"}})
        
        # 4. UTILS/ENS
        self.register_tool(name="resolve_ens", description="ENS: Resolve Name (Mainnet).", handler=resolve_ens, parameters={"name": {"type": "string"}, "rpc_url": {"type": "string"}})
        self.register_tool(name="to_wei", description="UTIL: Convert to Wei.", handler=to_wei, parameters={"amount": {"type": "number"}, "unit": {"type": "string"}})
        self.register_tool(name="from_wei", description="UTIL: Convert from Wei.", handler=from_wei, parameters={"amount": {"type": "number"}, "unit": {"type": "string"}})

        # --- 9. PHASE 6: YIELD & SAFETY ---
        from mcp_servers.web3_server.tools.staking import stake_eth_lido
        from mcp_servers.web3_server.tools.stableswap import get_curve_quote
        from mcp_servers.web3_server.tools.security import simulate_transaction
        
        self.register_tool(name="stake_eth_lido", description="YIELD: Stake ETH on Lido.", handler=stake_eth_lido, parameters={"amount": {"type": "number"}, "private_key": {"type": "string"}, "rpc_url": {"type": "string"}})
        self.register_tool(name="get_curve_quote", description="YIELD: Curve Stable Quote.", handler=get_curve_quote, parameters={"token_in": {"type": "string"}, "token_out": {"type": "string"}, "amount_in": {"type": "number"}, "rpc_url": {"type": "string"}})
        self.register_tool(name="simulate_transaction", description="SAFETY: Simulate Tx (Dry Run).", handler=simulate_transaction, parameters={"to_address": {"type": "string"}, "value": {"type": "number"}, "data": {"type": "string"}, "from_address": {"type": "string"}, "rpc_url": {"type": "string"}})
        
        # --- 8. PHASE 5: UNIVERSAL & IDENTITY ---
        from mcp_servers.web3_server.tools.contract_interaction import read_contract, decode_transaction
        from mcp_servers.web3_server.tools.identity import get_ens_reverse_record
        from mcp_servers.web3_server.tools.weth import wrap_eth, unwrap_eth
        
        self.register_tool(name="read_contract", description="UNIVERSAL: Call Any Contract View Function.", handler=read_contract, parameters={"address": {"type": "string"}, "function_signature": {"type": "string"}, "args": {"type": "array"}, "arg_types": {"type": "array"}, "return_types": {"type": "array"}, "rpc_url": {"type": "string"}})
        self.register_tool(name="decode_transaction", description="UNIVERSAL: Decode Input Data.", handler=decode_transaction, parameters={"tx_hash": {"type": "string"}, "abi": {"type": "string"}, "rpc_url": {"type": "string"}})
        
        self.register_tool(name="get_ens_reverse_record", description="IDENTITY: Address to Name.", handler=get_ens_reverse_record, parameters={"address": {"type": "string"}, "rpc_url": {"type": "string"}})
        
        self.register_tool(name="wrap_eth", description="WETH: Wrap ETH.", handler=wrap_eth, parameters={"amount": {"type": "number"}, "private_key": {"type": "string"}, "rpc_url": {"type": "string"}})
        self.register_tool(name="unwrap_eth", description="WETH: Unwrap WETH.", handler=unwrap_eth, parameters={"amount": {"type": "number"}, "private_key": {"type": "string"}, "rpc_url": {"type": "string"}})
        
        # --- 7. PHASE 4: LENDING & ORACLES ---
        from mcp_servers.web3_server.tools.lending import get_aave_reserve_data, get_aave_user_account_data
        from mcp_servers.web3_server.tools.oracle import get_chainlink_price
        
        self.register_tool(name="get_aave_reserve_data", description="LENDING: Aave V3 APY Data.", handler=get_aave_reserve_data, parameters={"asset": {"type": "string"}, "rpc_url": {"type": "string"}})
        self.register_tool(name="get_aave_user_account_data", description="LENDING: Aave User Health.", handler=get_aave_user_account_data, parameters={"user_address": {"type": "string"}, "rpc_url": {"type": "string"}})
        
        self.register_tool(name="get_chainlink_price", description="ORACLE: Chainlink Feed Price.", handler=get_chainlink_price, parameters={"feed_address": {"type": "string"}, "rpc_url": {"type": "string"}})
        
        # --- 6. PHASE 3: DEFI, EVENTS, ACTION ---
        from mcp_servers.web3_server.tools.defi import get_uniswap_price
        from mcp_servers.web3_server.tools.events import get_contract_events
        from mcp_servers.web3_server.tools.action import send_eth, approve_token
        from mcp_servers.web3_server.tools.wallet import generate_wallet
        from mcp_servers.web3_server.tools.gas import estimate_gas
        
        self.register_tool(name="get_uniswap_price", description="DEFI: Get Token Price (Uniswap V3).", handler=get_uniswap_price, parameters={"token_in": {"type": "string"}, "token_out": {"type": "string"}, "amount_in": {"type": "number"}, "fee": {"type": "integer"}, "rpc_url": {"type": "string"}})
        self.register_tool(name="get_contract_events", description="EVENTS: Get Contract Logs.", handler=get_contract_events, parameters={"address": {"type": "string"}, "from_block": {"type": "string"}, "topics": {"type": "array"}, "rpc_url": {"type": "string"}})
        
        self.register_tool(name="send_eth", description="ACTION: Send ETH (Native).", handler=send_eth, parameters={"to_address": {"type": "string"}, "amount": {"type": "number"}, "private_key": {"type": "string"}, "rpc_url": {"type": "string"}})
        self.register_tool(name="approve_token", description="ACTION: Approve Token Spender.", handler=approve_token, parameters={"token_address": {"type": "string"}, "spender_address": {"type": "string"}, "amount": {"type": "number"}, "private_key": {"type": "string"}, "rpc_url": {"type": "string"}})
        
        self.register_tool(name="generate_wallet", description="WALLET: Generate New Wallet.", handler=generate_wallet)
        self.register_tool(name="estimate_gas", description="GAS: Estimate Transaction Gas.", handler=estimate_gas, parameters={"to_address": {"type": "string"}, "data": {"type": "string"}, "value": {"type": "number"}, "rpc_url": {"type": "string"}})

        # 5. TOKEN SHORTCUTS (Top 15)
        # Mainnet Addresses
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
            "steth": "0xae7ab96520DE3A18E5e111B5Ee5B82061ZL270310", # Intentional typo to test error handling? No, copy paste carefully. 0xae7ab96520DE3A18E5e111B5Ee5B82061ce70310
            "fet": "0xaea46A60368A7bD060eec7DF8CBa43b7EF41Ad85",
            "rndr": "0x6De037ef9aD2725EB404906F1CC53138EA7Fb6E5",
            "aave": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"
        }
        
        # Valid stETH: 0xae7ab96520DE3A18E5e111B5Ee5B82061ce70310
        tokens['steth'] = "0xae7ab96520DE3A18E5e111B5Ee5B82061ce70310"

        for sym, addr in tokens.items():
            # Balance Shortcut
            tool_name = f"get_{sym}_balance"
            async def token_handler(args: dict, a=addr) -> ToolResult:
                args['token_address'] = a
                return await get_token_balance(args)
            
            self.register_tool(name=tool_name, description=f"SHORTCUT: Get {sym.upper()} Balance.", handler=token_handler, parameters={"wallet_address": {"type": "string"}})
            
            # Price Shortcut (Uniswap V3 vs USDC/WETH)
            # Default to pricing against USDC
            tool_name_price = f"get_{sym}_price"
            async def price_handler(args: dict, a=addr) -> ToolResult:
                args['token_in'] = a
                args['token_out'] = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48" # USDC
                return await get_uniswap_price(args)
            # Shortcut for stablecoins? USDC vs USDT
            
            self.register_tool(name=tool_name_price, description=f"SHORTCUT: Get {sym.upper()} Price (in USDC).", handler=price_handler)


            # Aave Shortcut (Reserve Data)
            tool_name_aave = f"get_{sym}_aave_data"
            async def aave_handler(args: dict, a=addr) -> ToolResult:
                args['asset'] = a
                return await get_aave_reserve_data(args)
            self.register_tool(name=tool_name_aave, description=f"SHORTCUT: Get {sym.upper()} Aave Rates.", handler=aave_handler)
            
            # Chainlink Shortcut (Requires mapping feed addresses... skipping for loop unless I map them all)
            # Instead, just register ETH USD and BTC USD manually below loop
            

        # Chainlink Shortcuts (Mainnet)
        # ETH/USD
        async def cl_eth_usd(args: dict) -> ToolResult:
            args['feed_address'] = "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419"
            return await get_chainlink_price(args)
        self.register_tool(name="get_chainlink_eth_usd", description="SHORTCUT: Chainlink ETH/USD.", handler=cl_eth_usd)
        
        # BTC/USD
        async def cl_btc_usd(args: dict) -> ToolResult:
            args['feed_address'] = "0xF4030086522a5bEEa4988F8cA5B36dbC97BeE88c"
            return await get_chainlink_price(args)
        self.register_tool(name="get_chainlink_btc_usd", description="SHORTCUT: Chainlink BTC/USD.", handler=cl_btc_usd)
        
        # USDC/USD
        async def cl_usdc_usd(args: dict) -> ToolResult:
            args['feed_address'] = "0x8fFfFfd4AfB6115b954Bd326cbe7B4BA576818f6"
            return await get_chainlink_price(args)
        self.register_tool(name="get_chainlink_usdc_usd", description="SHORTCUT: Chainlink USDC/USD.", handler=cl_usdc_usd)

if __name__ == "__main__":
    import asyncio
    server = Web3Server()
    asyncio.run(server.run())
