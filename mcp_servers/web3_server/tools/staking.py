
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.web3_server.tools.network import get_web3_instance
from eth_account import Account

LIDO_PROXY_ADDRESS = "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84"
LIDO_ABI = [{"constant":False,"inputs":[{"name":"_referral","type":"address"}],"name":"submit","outputs":[{"name":"","type":"uint256"}],"payable":True,"stateMutability":"payable","type":"function"}]

async def stake_eth_lido(arguments: dict) -> ToolResult:
    """
    Stake ETH with Lido (Get stETH).
    """
    amount_eth = float(arguments.get("amount"))
    private_key = arguments.get("private_key")
    referral = arguments.get("referral", "0x0000000000000000000000000000000000000000")
    
    try:
        w3 = await get_web3_instance(arguments)
        account = Account.from_key(private_key)
        lido = w3.eth.contract(address=LIDO_PROXY_ADDRESS, abi=LIDO_ABI)
        
        amount_wei = w3.to_wei(amount_eth, 'ether')
        
        tx = await lido.functions.submit(w3.to_checksum_address(referral)).build_transaction({
            'from': account.address,
            'value': amount_wei,
            'nonce': await w3.eth.get_transaction_count(account.address),
            'gasPrice': await w3.eth.gas_price
        })
        
        signed = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = await w3.eth.send_raw_transaction(signed.rawTransaction)
        
        return ToolResult(content=[TextContent(text=f"### Staked ETH (Lido)\n**Hash**: {tx_hash.hex()}\n**Amount**: {amount_eth} ETH")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
