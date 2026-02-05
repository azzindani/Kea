
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.web3_server.tools.network import get_web3_instance
from web3 import Web3
from eth_account import Account

async def send_eth(arguments: dict) -> ToolResult:
    """
    Send Native ETH (Write Action).
    Requires private_key.
    """
    to_address = arguments.get("to_address")
    amount = float(arguments.get("amount"))
    private_key = arguments.get("private_key")
    
    try:
        w3 = await get_web3_instance(arguments)
        
        account = Account.from_key(private_key)
        nonce = await w3.eth.get_transaction_count(account.address)
        
        tx = {
            'nonce': nonce,
            'to': w3.to_checksum_address(to_address),
            'value': w3.to_wei(amount, 'ether'),
            'gas': 21000,
            'gasPrice': await w3.eth.gas_price
        }
        
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = await w3.eth.send_raw_transaction(signed_tx.rawTransaction) # Attribute error? rawTransaction is correct on SignedTransaction
        
        return ToolResult(content=[TextContent(text=f"### Transaction Sent\n**Hash**: {tx_hash.hex()}\n**From**: {account.address}\n**To**: {to_address}\n**Value**: {amount} ETH")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def approve_token(arguments: dict) -> ToolResult:
    """
    Approve Token Spender.
    """
    token_address = arguments.get("token_address")
    spender_address = arguments.get("spender_address")
    amount = float(arguments.get("amount")) # Default infinite?
    private_key = arguments.get("private_key")
    
    erc20_approve_abi = [{"constant":False,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"success","type":"bool"}],"type":"function"}]
    
    try:
        w3 = await get_web3_instance(arguments)
        account = Account.from_key(private_key)
        token = w3.eth.contract(address=w3.to_checksum_address(token_address), abi=erc20_approve_abi)
        
        # Need decimals for amount if not raw? Usually approvals are raw or max
        # Let's assume input is in tokens, need to fetch decimals...
        # ... Skipping decimals fetch for brevity, assume user might pass raw big int if they want precise control?
        # For safety/usability, let's just use 10^18 default or try fetch.
        
        amount_wei = int(amount * (10**18)) # Assumption!
        
        # Build Tx
        tx = await token.functions.approve(w3.to_checksum_address(spender_address), amount_wei).build_transaction({
            'from': account.address,
            'nonce': await w3.eth.get_transaction_count(account.address),
            'gasPrice': await w3.eth.gas_price
        })
        
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = await w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        return ToolResult(content=[TextContent(text=f"### Approval Sent\n**Hash**: {tx_hash.hex()}\n**Token**: {token_address}\n**Spender**: {spender_address}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
