
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.web3_server.tools.network import get_web3_instance
from web3 import Web3
import json

async def get_block(arguments: dict) -> ToolResult:
    """
    Get Block Information.
    """
    block_id = arguments.get("block_id", "latest") # number or 'latest'
    full_tx = arguments.get("full_transactions", false) # Boolean in python is False/True
    
    # Arguments from MCP come as json values, careful with bools
    full_tx = bool(arguments.get("full_transactions", False))
    
    try:
        w3 = await get_web3_instance(arguments)
        
        # Determine if block_id is hash or number
        if str(block_id).startswith("0x"):
            block = await w3.eth.get_block(block_id, full_transactions=full_tx)
        elif str(block_id).lower() in ['latest', 'earliest', 'pending']:
             block = await w3.eth.get_block(block_id, full_transactions=full_tx)
        else:
             block = await w3.eth.get_block(int(block_id), full_transactions=full_tx)
             
        # Convert AttributeDict to dict for JSON serialization
        block_dict = dict(block)
        # Handle bytes conversion
        block_json = Web3.to_json(block_dict) 
        
        # Summary view
        tx_count = len(block_dict.get('transactions', []))
        summary = f"""### Block {block_dict.get('number')}
**Hash**: {block_dict.get('hash').hex() if hasattr(block_dict.get('hash'), 'hex') else block_dict.get('hash')}
**Parent**: {block_dict.get('parentHash').hex() if hasattr(block_dict.get('parentHash'), 'hex') else block_dict.get('parentHash')}
**Time**: {block_dict.get('timestamp')}
**Transactions**: {tx_count}
**Gas Used**: {block_dict.get('gasUsed')} / {block_dict.get('gasLimit')}

```json
{block_json}
```
"""
        return ToolResult(content=[TextContent(text=summary)])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_transaction(arguments: dict) -> ToolResult:
    """
    Get Transaction Details by Hash.
    """
    tx_hash = arguments.get("tx_hash")
    
    try:
        w3 = await get_web3_instance(arguments)
        tx = await w3.eth.get_transaction(tx_hash)
        
        # Receipt often needed too
        try:
            receipt = await w3.eth.get_transaction_receipt(tx_hash)
            receipt_json = Web3.to_json(dict(receipt))
        except:
            receipt_json = "Pending/Not Found"
            
        tx_json = Web3.to_json(dict(tx))
        
        return ToolResult(content=[TextContent(text=f"### Transaction\n**Hash**: {tx_hash}\n\n**Data**:\n```json\n{tx_json}\n```\n\n**Receipt**:\n```json\n{receipt_json}\n```")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_balance(arguments: dict) -> ToolResult:
    """
    Get Native (ETH) Balance.
    """
    address = arguments.get("address")
    block_id = arguments.get("block_id", "latest")
    
    try:
        w3 = await get_web3_instance(arguments)
        if not w3.is_address(address):
             return ToolResult(isError=True, content=[TextContent(text="Invalid Address")])
             
        # Resolve ENS if supported later, for now raw address
        checksum_addr = w3.to_checksum_address(address)
        
        balance_wei = await w3.eth.get_balance(checksum_addr, block_identifier=block_id)
        balance_eth = w3.from_wei(balance_wei, 'ether')
        
        return ToolResult(content=[TextContent(text=f"### Balance\n**Address**: {address}\n**Balance**: {balance_eth} ETH\n**Wei**: {balance_wei}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_gas_price(arguments: dict) -> ToolResult:
    """
    Get Current Gas Price / Fee Data.
    """
    try:
        w3 = await get_web3_instance(arguments)
        
        gas_price = await w3.eth.gas_price
        gas_gwei = w3.from_wei(gas_price, 'gwei')
        
        # EIP-1559 check
        try:
             fees = await w3.eth.max_priority_fee_per_gas
             priority_gwei = w3.from_wei(fees, 'gwei')
        except:
             priority_gwei = "N/A"
             
        return ToolResult(content=[TextContent(text=f"### Gas Price\n**Legacy**: {gas_gwei} Gwei\n**Priority**: {priority_gwei} Gwei")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_block_number(arguments: dict) -> ToolResult:
    """Get Current Block Number."""
    try:
        w3 = await get_web3_instance(arguments)
        num = await w3.eth.block_number
        return ToolResult(content=[TextContent(text=str(num))])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_transaction_count(arguments: dict) -> ToolResult:
    """Get Transaction Count (Nonce)."""
    address = arguments.get("address")
    try:
        w3 = await get_web3_instance(arguments)
        count = await w3.eth.get_transaction_count(w3.to_checksum_address(address))
        return ToolResult(content=[TextContent(text=str(count))])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_chain_id(arguments: dict) -> ToolResult:
    """Get Chain ID."""
    try:
        w3 = await get_web3_instance(arguments)
        chain_id = await w3.eth.chain_id
        return ToolResult(content=[TextContent(text=str(chain_id))])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_code(arguments: dict) -> ToolResult:
    """Get Smart Contract Code."""
    address = arguments.get("address")
    try:
        w3 = await get_web3_instance(arguments)
        code = await w3.eth.get_code(w3.to_checksum_address(address))
        return ToolResult(content=[TextContent(text=code.hex())])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
