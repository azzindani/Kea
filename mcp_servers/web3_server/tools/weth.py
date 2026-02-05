
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.web3_server.tools.network import get_web3_instance
from eth_account import Account

WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2" # Mainnet
WETH_ABI = [{"constant":False,"inputs":[],"name":"deposit","outputs":[],"payable":True,"stateMutability":"payable","type":"function"},{"constant":False,"inputs":[{"name":"wad","type":"uint256"}],"name":"withdraw","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"}]

async def wrap_eth(arguments: dict) -> ToolResult:
    """
    Wrap ETH to WETH.
    """
    amount_eth = float(arguments.get("amount"))
    private_key = arguments.get("private_key")
    
    try:
        w3 = await get_web3_instance(arguments)
        account = Account.from_key(private_key)
        weth = w3.eth.contract(address=WETH_ADDRESS, abi=WETH_ABI)
        
        amount_wei = w3.to_wei(amount_eth, 'ether')
        
        tx = await weth.functions.deposit().build_transaction({
            'from': account.address,
            'value': amount_wei,
            'nonce': await w3.eth.get_transaction_count(account.address),
            'gasPrice': await w3.eth.gas_price
        })
        
        signed = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = await w3.eth.send_raw_transaction(signed.rawTransaction)
        
        return ToolResult(content=[TextContent(text=f"### Wrapped ETH\n**Hash**: {tx_hash.hex()}\n**Amount**: {amount_eth} ETH -> WETH")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def unwrap_eth(arguments: dict) -> ToolResult:
    """
    Unwrap WETH to ETH.
    """
    amount_weth = float(arguments.get("amount"))
    private_key = arguments.get("private_key")
    
    try:
        w3 = await get_web3_instance(arguments)
        account = Account.from_key(private_key)
        weth = w3.eth.contract(address=WETH_ADDRESS, abi=WETH_ABI)
        
        amount_wei = w3.to_wei(amount_weth, 'ether')
        
        tx = await weth.functions.withdraw(amount_wei).build_transaction({
            'from': account.address,
            'nonce': await w3.eth.get_transaction_count(account.address),
            'gasPrice': await w3.eth.gas_price
        })
        
        signed = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = await w3.eth.send_raw_transaction(signed.rawTransaction)
        
        return ToolResult(content=[TextContent(text=f"### Unwrapped WETH\n**Hash**: {tx_hash.hex()}\n**Amount**: {amount_weth} WETH -> ETH")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
