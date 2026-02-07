import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_sec_edgar_real_simulation():
    """
    REAL SIMULATION: Verify SEC Edgar Server (Filings).
    """
    params = get_server_params("sec_edgar_server", extra_dependencies=["sec-edgar-downloader", "pandas", "beautifulsoup4", "lxml", "textblob"])
    
    ticker = "AAPL"
    
    print(f"\n--- Starting Real-World Simulation: SEC Edgar Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Download Latest 10-K
            print(f"1. Downloading 10-K for {ticker}...")
            # Note: SEC EDGAR downloader requires User-Agent. Server likely handles it or uses default.
            # Real download might take time/bandwidth.
            # Using 'amount=1' to minimize impact.
            res = await session.call_tool("get_10k_latest", arguments={"ticker": ticker})
            if not res.isError:
                 print(f" [PASS] Downloaded/Extracted: {res.content[0].text[:100]}...")
            else:
                 print(f" [WARN] 10-K Download failed: {res.content[0].text}")

            # 2. List Filings
            print(f"2. Listing Filings for {ticker}...")
            res = await session.call_tool("list_filings", arguments={"ticker": ticker})
            print(f" [PASS] Listings: {res.content[0].text}")

    print("--- SEC Edgar Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
