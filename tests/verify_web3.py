
import asyncio
from mcp_servers.web3_server.server import Web3Server
from mcp_servers.web3_server.tools.network import NetworkManager

# Known addresses
VITALIK = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
USDT_ETH = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
FOUNDATION = "0xDE0B295669a9FD93d5F28D9Ec85E40f4cb697BAe"

async def verify():
    print("--- Verifying Web3 Server (Real RPC) ---")
    server = Web3Server()
    # Check connection first
    try:
        w3 = await NetworkManager.get_web3("https://eth.llamarpc.com")
        if not await w3.is_connected():
            print("SKIPPING: Could not connect to RPC. Environment restricted?")
            return
        
        print("Connected to Ethereum Mainnet!")
        
        # Test 1: Get Balance
        print("\n--- 1. Get Balance (Vitalik) ---")
        try:
            handler = server._handlers["get_balance"]
            res = await handler({"address": VITALIK})
            if not res.isError:
                 print("SUCCESS:", res.content[0].text)
            else:
                 print("FAILED:", res.content[0].text)
        except Exception as e:
            print(f"Exception: {e}")
            
        # Test 2: Get Token Metadata (USDT)
        print("\n--- 2. Get Token Metadata (USDT) ---")
        try:
            handler = server._handlers["get_token_metadata"]
            res = await handler({"token_address": USDT_ETH})
            if not res.isError:
                 print("SUCCESS:", res.content[0].text)
            else:
                 print("FAILED:", res.content[0].text)
        except Exception as e:
            print(f"Exception: {e}")
            
        # Test 3: Multicall Bulk Balances
        print("\n--- 3. Multicall Bulk Balances (Vitalik, Foundation) ---")
        try:
            handler = server._handlers["get_bulk_balances"]
            res = await handler({"addresses": [VITALIK, FOUNDATION]})
            if not res.isError:
                 print("SUCCESS:", res.content[0].text[:100] + "...")
            else:
                 print("FAILED:", res.content[0].text)
        except Exception as e:
            print(f"Exception: {e}")

        # Test 4: Uniswap Price (DeFi)
        print("\n--- 4. Uniswap Price (WETH -> USDC) ---")
        try:
            handler = server._handlers["get_uniswap_price"]
            # WETH -> USDC
            res = await handler({"token_in": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", "token_out": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "amount_in": 1})
            if not res.isError:
                 print("SUCCESS:", res.content[0].text)
            else:
                 print("FAILED:", res.content[0].text)
        except Exception as e:
            print(f"Exception: {e}")
            
        # Test 5: Aave Data (Lending)
        print("\n--- 5. Aave Reserve Data (USDC) ---")
        try:
            handler = server._handlers["get_aave_reserve_data"]
            res = await handler({"asset": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"})
            if not res.isError:
                 print("SUCCESS:", res.content[0].text)
            else:
                 print("FAILED:", res.content[0].text)
        except Exception as e:
            print(f"Exception: {e}")
            
        # Test 6: Chainlink Oracle
        print("\n--- 6. Chainlink Oracle (ETH/USD) ---")
        try:
            handler = server._handlers["get_chainlink_eth_usd"]
            res = await handler({})
            if not res.isError:
                 print("SUCCESS:", res.content[0].text)
            else:
                 print("FAILED:", res.content[0].text)
        except Exception as e:
            print(f"Exception: {e}")
            
        # Test 7: Universal Read
        print("\n--- 7. Universal Read (USDT TotalSupply) ---")
        try:
            handler = server._handlers["read_contract"]
            res = await handler({
                "address": USDT_ETH,
                "function_signature": "totalSupply()",
                "return_types": ["uint256"]
            })
            if not res.isError:
                 print("SUCCESS:", res.content[0].text)
            else:
                 print("FAILED:", res.content[0].text)
        except Exception as e:
            print(f"Exception: {e}")
            
    except Exception as e:
        print(f"General Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
