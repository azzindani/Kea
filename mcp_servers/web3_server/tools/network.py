
from web3 import Web3, AsyncWeb3
from shared.logging import get_logger
from shared.mcp.protocol import ToolResult, TextContent

logger = get_logger(__name__)

class NetworkManager:
    _instance = None
    _w3 = None
    
    # Default Public RPC (Ethereum Mainnet)
    # Using LlamaRPC or Cloudflare as they are reliable and free
    DEFAULT_RPC = "https://eth.llamarpc.com"
    
    @classmethod
    async def get_web3(cls, rpc_url=None):
        if cls._w3 is None:
            rpc = rpc_url or cls.DEFAULT_RPC
            logger.info(f"Initializing Web3 with RPC: {rpc}")
            # Use AsyncWeb3 for async support
            cls._w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(rpc))
            
            # Check connection
            if await cls._w3.is_connected():
                logger.info("Web3 Connected successfully.")
            else:
                logger.error("Web3 Connection failed.")
                
        return cls._w3
        
    @classmethod
    async def set_rpc(cls, rpc_url):
        cls.DEFAULT_RPC = rpc_url
        # Reset instance to force reconnection
        cls._w3 = None
        logger.info(f"Switched RPC to: {rpc_url}")

async def get_web3_instance(arguments: dict = None):
    rpc = arguments.get("rpc_url") if arguments else None
    return await NetworkManager.get_web3(rpc)

async def switch_chain(arguments: dict) -> ToolResult:
    """
    Switch Default Network (RPC).
    """
    chain = arguments.get("chain", "ethereum").lower()
    
    chains = {
        "ethereum": "https://eth.llamarpc.com",
        "arbitrum": "https://arb1.arbitrum.io/rpc",
        "optimism": "https://mainnet.optimism.io",
        "polygon": "https://polygon-rpc.com",
        "bsc": "https://binance.llamarpc.com",
        "base": "https://mainnet.base.org",
        "avalanche": "https://api.avax.network/ext/bc/C/rpc"
    }
    
    rpc = chains.get(chain)
    if not rpc:
        # Check if custom url
        if chain.startswith("http"):
            rpc = chain
        else:
            return ToolResult(isError=True, content=[TextContent(text=f"Unknown chain: {chain}. Supported: {list(chains.keys())}")])
            
    await NetworkManager.set_rpc(rpc)
    return ToolResult(content=[TextContent(text=f"Switched to {chain} ({rpc})")])
