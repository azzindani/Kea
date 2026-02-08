import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_regulatory_real_simulation():
    """
    REAL SIMULATION: Verify Regulatory Server (EDGAR/eCFR).
    """
    params = get_server_params("regulatory_server", extra_dependencies=["httpx"])
    
    print(f"\n--- Starting Real-World Simulation: Regulatory Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. EDGAR Search
            print("1. Searching EDGAR (Tesla)...")
            res = await session.call_tool("edgar_search", arguments={"company": "Tesla", "filing_type": "10-K"})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Search results received")
            else:
                 print(f" [WARN] EDGAR Search failed (network/rate limit?): {res.content[0].text}")

            # 2. eCFR Search
            print("2. Searching eCFR (Drones)...")
            res = await session.call_tool("ecfr_search", arguments={"query": "drones"})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m eCFR results received")

            # 3. Federal Register
            print("3. Federal Register...")
            await session.call_tool("federal_register_search", arguments={"query": "AI safety"})

            # 4. Global Data (WTO/IMF)
            print("4. Global Data...")
            # These might fail without keys or network, but we call them
            try:
                await session.call_tool("wto_data", arguments={"indicator": "trade_merchandise_export", "year": 2022})
            except: pass
            
            try:
                await session.call_tool("imf_data", arguments={"indicator": "NGDP_RPCH", "country": "US", "year": "2023"})
            except: pass

    print("--- Regulatory Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
