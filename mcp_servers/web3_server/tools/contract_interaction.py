
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.web3_server.tools.network import get_web3_instance
from web3 import Web3
import json

async def read_contract(arguments: dict) -> ToolResult:
    """
    Call ANY Contract View Function.
    Requires: address, function_signature (e.g. "decimals()"), return_types (list of types e.g. ["uint256"]).
    OR provide full ABI.
    """
    address = arguments.get("address")
    function_sig = arguments.get("function_signature") # e.g. "balanceOf(address)"
    function_args = arguments.get("args", []) # List of args
    return_types = arguments.get("return_types", ["uint256"]) # List of string types
    abi_json = arguments.get("abi") # Optional full ABI string
    
    try:
        w3 = await get_web3_instance(arguments)
        checksum_addr = w3.to_checksum_address(address)
        
        if abi_json:
             abi = json.loads(abi_json)
             contract = w3.eth.contract(address=checksum_addr, abi=abi)
             # Need function name. If ABI provided, maybe just use function name?
             # For now, stick to manual decoding if sig provided, or use standard web3 if abi provided + func name
             # This tool is tricky to make "Universal" simply.
             # Approach: Construct 4byte selector + encode args manually.
             pass
             
        # Manual Encoding Approach (Universal)
        # 1. Parse signature to get selector
        selector = w3.keccak(text=function_sig)[:4].hex()
        
        # 2. Encode Args
        # Need types from signature... "transfer(address,uint256)" -> ["address", "uint256"]
        # Simple parser or user provides "arg_types"?
        # Let's assume user provides arg_types.
        arg_types = arguments.get("arg_types", [])
        
        from eth_abi import encode, decode
        
        encoded_args = encode(arg_types, function_args)
        data = selector + encoded_args.hex()
        
        # 3. Call
        raw_result = await w3.eth.call({
            "to": checksum_addr,
            "data": data
        })
        
        # 4. Decode Output
        decoded = decode(return_types, raw_result)
        
        return ToolResult(content=[TextContent(text=f"### Contract Read\n**Function**: {function_sig}\n**Result**: {decoded}")])
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=f"Read Error: {str(e)}. Ensure arg_types/return_types match signature.")])

async def decode_transaction(arguments: dict) -> ToolResult:
    """
    Decode Transaction Input Data.
    """
    tx_hash = arguments.get("tx_hash")
    abi_json = arguments.get("abi") # Optional
    
    try:
        w3 = await get_web3_instance(arguments)
        tx = await w3.eth.get_transaction(tx_hash)
        input_data = tx['input']
        
        if abi_json:
            abi = json.loads(abi_json)
            contract = w3.eth.contract(abi=abi)
            func_obj, func_params = contract.decode_function_input(input_data)
            return ToolResult(content=[TextContent(text=f"### Decoded Input\n**Function**: {func_obj.fn_name}\n**Params**: {func_params}")])
        else:
            selector = input_data[:10] # 0x + 8 chars
            return ToolResult(content=[TextContent(text=f"### Raw Input\n**Selector**: {selector}\n**Raw API**: Provide ABI to decode fully.\n**Data**: {input_data}")])
            
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
