
from edgar import set_identity
from mcp_servers.python_edgar_server.tools.xbrl_deep import get_xbrl_tag_values, search_xbrl_tags
from mcp_servers.python_edgar_server.tools.funds import get_fund_portfolio
import asyncio

set_identity("Kea Agent <kea@antigravity.dev>")

async def verify():
    print("--- Verifying Phase 4 (Deep XBRL) & 5 (Funds) ---")
    
    # 1. Search Tags
    print("\n1. Searching XBRL Tags (AAPL, 'Entity')...")
    res1 = await search_xbrl_tags({'ticker': 'AAPL', 'query': 'Entity'})
    print(str(res1)[:300])
    
    # 2. Get Tag Values
    print("\n2. Getting 'EntityCommonStockSharesOutstanding' (AAPL)...")
    res2 = await get_xbrl_tag_values({'ticker': 'AAPL', 'tag': 'EntityCommonStockSharesOutstanding'})
    print(str(res2)[:500])
    
    # 3. Fund Portfolio
    print("\n3. Getting Fund Portfolio (BRK-B)...")
    res3 = await get_fund_portfolio({'ticker': 'BRK-B'})
    # This might fail if BRK-B doesn't map well in edgar, try CIK if needed
    # BRK CIK: 0001067983
    if res3.isError:
         print(f"Retry with CIK for Berkshire...")
         res3 = await get_fund_portfolio({'ticker': '1067983'})
         
    print(str(res3)[:500])

if __name__ == "__main__":
    asyncio.run(verify())
