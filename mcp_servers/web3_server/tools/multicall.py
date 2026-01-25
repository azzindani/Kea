
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.web3_server.tools.network import get_web3_instance
from web3 import Web3
import asyncio
import pandas as pd

# Multicall3 Address (Same on mainnet, arb, op, polygon, bsc, etc.)
MULTICALL3_ADDRESS = "0xcA11bde05977b3631167028862bE2a173976CA11"

MULTICALL3_ABI = [
    {
        "inputs": [{"components": [{"internalType": "address", "name": "target", "type": "address"}, {"internalType": "bool", "name": "allowFailure", "type": "bool"}, {"internalType": "bytes", "name": "callData", "type": "bytes"}], "internalType": "struct Multicall3.Call3[]", "name": "calls", "type": "tuple[]"}],
        "name": "aggregate3",
        "outputs": [{"components": [{"internalType": "bool", "name": "success", "type": "bool"}, {"internalType": "bytes", "name": "returnData", "type": "bytes"}], "internalType": "struct Multicall3.Result[]", "name": "returnData", "type": "tuple[]"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "addr", "type": "address"}],
        "name": "getEthBalance",
        "outputs": [{"internalType": "uint256", "name": "balance", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

async def get_bulk_balances(arguments: dict) -> ToolResult:
    """
    Get ETH Balances for multiple addresses in ONE call.
    Uses Multicall3 `aggregate3` + `getEthBalance` helper.
    """
    addresses = arguments.get("addresses") # List of strings
    
    try:
        w3 = await get_web3_instance(arguments)
        mc_contract = w3.eth.contract(address=MULTICALL3_ADDRESS, abi=MULTICALL3_ABI)
        
        calls = []
        for addr in addresses:
            # We call Multicall3's own 'getEthBalance' helper function which is cheaper/easier
            # Encode the call: target is Multicall3 itself, function is getEthBalance
            # Wait, aggregate3 takes (target, allowFailure, callData)
            # We want to call 'getEthBalance(addr)' on Multicall3
            
            call_data = mc_contract.encode_abi(fn_name="getEthBalance", args=[w3.to_checksum_address(addr)])
            calls.append((MULTICALL3_ADDRESS, True, call_data))
            
        # Execute
        results = await mc_contract.functions.aggregate3(calls).call()
        
        data = []
        for i, res in enumerate(results):
            success, return_data = res
            addr = addresses[i]
            if success:
                # Decode uint256
                balance_wei = int.from_bytes(return_data, byteorder='big')
                balance_eth = w3.from_wei(balance_wei, 'ether')
                data.append({"address": addr, "balance": float(balance_eth), "wei": balance_wei})
            else:
                data.append({"address": addr, "balance": None, "error": "Failed"})
                
        df = pd.DataFrame(data)
        
        return ToolResult(content=[TextContent(text=f"### Bulk ETH Balances ({len(addresses)})\n\n{df.to_markdown()}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_bulk_token_balances(arguments: dict) -> ToolResult:
    """
    Get Token Balances for ONE address across MULTIPLE tokens.
    """
    wallet = arguments.get("wallet_address")
    tokens = arguments.get("token_addresses") # List
    
    # ERC20 balanceOf ABI
    erc20_abi_frag = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]
    
    try:
        w3 = await get_web3_instance(arguments)
        mc_contract = w3.eth.contract(address=MULTICALL3_ADDRESS, abi=MULTICALL3_ABI)
        dummy_contract = w3.eth.contract(abi=erc20_abi_frag) # Just for encoding
        
        wallet_checksum = w3.to_checksum_address(wallet)
        
        calls = []
        for token in tokens:
            token_checksum = w3.to_checksum_address(token)
            # Encode balanceOf(wallet)
            call_data = dummy_contract.encode_abi(fn_name="balanceOf", args=[wallet_checksum])
            calls.append((token_checksum, True, call_data))
            
        results = await mc_contract.functions.aggregate3(calls).call()
        
        data = []
        for i, res in enumerate(results):
            success, return_data = res
            token = tokens[i]
            if success and len(return_data) > 0:
                balance_raw = int.from_bytes(return_data, byteorder='big')
                # Note: We don't know decimals here easily without another multicall. 
                # For high efficiency, user should ask for metadata separately or we return raw.
                data.append({"token": token, "raw_balance": balance_raw})
            else:
                data.append({"token": token, "raw_balance": 0, "status": "Failed/Zero"})
                
        df = pd.DataFrame(data)
        return ToolResult(content=[TextContent(text=f"### Bulk Token Balances\n**Wallet**: {wallet}\n\n{df.to_markdown()}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
