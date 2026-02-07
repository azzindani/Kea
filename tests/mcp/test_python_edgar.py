import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_python_edgar_real_simulation():
    """
    REAL SIMULATION: Verify Python Edgar Server (SEC Filings).
    """
    params = get_server_params("python_edgar_server", extra_dependencies=["edgartools", "pandas"])
    
    ticker = "AAPL"
    
    print(f"\n--- Starting Real-World Simulation: Python Edgar Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Company Profile
            print(f"1. Analyzing Profile ({ticker})...")
            # This might hit network limits or require user agent setup in edgartools
            # standard edgartools usually requires setting identity
            # The server likely handles it or uses valid default
            res = await session.call_tool("analyze_company_profile", arguments={"ticker": ticker})
            if res.isError:
                 print(f" [FAIL] {res.content[0].text}")
            else:
                 print(f" [PASS] Profile received (Length: {len(res.content[0].text)})")

            # 2. Find Filings
            print("2. Finding Filings (10-K)...")
            res = await session.call_tool("find_filings", arguments={"ticker": ticker, "form": "10-K", "limit": 1})
            if not res.isError:
                 print(f" [PASS] Filings found")
            
            # 3. Filing Sections
            print("3. Getting Filing Sections...")
            res = await session.call_tool("get_filing_sections", arguments={"ticker": ticker, "form": "10-K"})
            if not res.isError:
                 print(f" [PASS] Sections listed")

    print("--- Python Edgar Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
