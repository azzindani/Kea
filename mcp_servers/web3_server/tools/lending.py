
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.web3_server.tools.network import get_web3_instance
from web3 import Web3

# Aave V3 PoolDataProvider (Mainnet)
POOL_DATA_PROVIDER_ADDRESS = "0x7B4EB56E7CD4b454BA8ff71E4518426369a138a3"
# Aave V3 Pool (Mainnet) - For user account data
POOL_ADDRESS = "0x87870Bca3F3f638F9947C416301e724D94f4a58C"

# Minimal ABIs
DATA_PROVIDER_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "asset", "type": "address"}],
        "name": "getReserveData",
        "outputs": [
            {"internalType": "uint256", "name": "unbacked", "type": "uint256"},
            {"internalType": "uint256", "name": "accruedToTreasuryScaled", "type": "uint256"},
            {"internalType": "uint256", "name": "totalAToken", "type": "uint256"},
            {"internalType": "uint256", "name": "totalStableDebt", "type": "uint256"},
            {"internalType": "uint256", "name": "totalVariableDebt", "type": "uint256"},
            {"internalType": "uint256", "name": "liquidityRate", "type": "uint256"},
            {"internalType": "uint256", "name": "variableBorrowRate", "type": "uint256"},
            {"internalType": "uint256", "name": "stableBorrowRate", "type": "uint256"},
            {"internalType": "uint256", "name": "averageStableBorrowRate", "type": "uint256"},
            {"internalType": "uint256", "name": "liquidityIndex", "type": "uint256"},
            {"internalType": "uint256", "name": "variableBorrowIndex", "type": "uint256"},
            {"internalType": "uint40", "name": "lastUpdateTimestamp", "type": "uint40"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

POOL_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
        "name": "getUserAccountData",
        "outputs": [
            {"internalType": "uint256", "name": "totalCollateralBase", "type": "uint256"},
            {"internalType": "uint256", "name": "totalDebtBase", "type": "uint256"},
            {"internalType": "uint256", "name": "availableBorrowsBase", "type": "uint256"},
            {"internalType": "uint256", "name": "currentLiquidationThreshold", "type": "uint256"},
            {"internalType": "uint256", "name": "ltv", "type": "uint256"},
            {"internalType": "uint256", "name": "healthFactor", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

async def get_aave_reserve_data(arguments: dict) -> ToolResult:
    """
    Get Aave V3 Reserve Data (APYs).
    Requires Asset Address (e.g. USDC).
    Yields are in Ray units (1e27).
    """
    asset = arguments.get("asset")
    
    try:
        w3 = await get_web3_instance(arguments)
        
        # Note: Address checks
        provider = w3.eth.contract(address=POOL_DATA_PROVIDER_ADDRESS, abi=DATA_PROVIDER_ABI)
        
        data = await provider.functions.getReserveData(w3.to_checksum_address(asset)).call()
        # [0] unbacked, ...
        # [5] liquidityRate (Deposit APY)
        # [6] variableBorrowRate (Borrow APY)
        
        deposit_apy = float(data[5]) / 10**27
        borrow_apy = float(data[6]) / 10**27
        
        # Total Liquidity (AToken)
        total_supply = data[2]
        
        return ToolResult(content=[TextContent(text=f"### Aave V3 Data\n**Asset**: {asset}\n**Deposit APY**: {deposit_apy:.2%}\n**Borrow APY**: {borrow_apy:.2%}\n**Total Supply (Raw)**: {total_supply}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=f"Aave Error: {str(e)}. (Note: Mainnet addresses hardcoded).")])

async def get_aave_user_account_data(arguments: dict) -> ToolResult:
    """
    Get Aave V3 User Health Factor.
    """
    user = arguments.get("user_address")
    
    try:
        w3 = await get_web3_instance(arguments)
        pool = w3.eth.contract(address=POOL_ADDRESS, abi=POOL_ABI)
        
        data = await pool.functions.getUserAccountData(w3.to_checksum_address(user)).call()
        
        health_factor = float(data[5]) / 10**18
        # Collateral is in Base Currency (USD usually 8 decimals)
        collateral_usd = float(data[0]) / 10**8
        debt_usd = float(data[1]) / 10**8
        
        return ToolResult(content=[TextContent(text=f"### Aave User Data\n**User**: {user}\n**Health Factor**: {health_factor:.2f}\n**Collateral**: ${collateral_usd:,.2f}\n**Debt**: ${debt_usd:,.2f}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
