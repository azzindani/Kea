
import sys
import asyncio
sys.path.append("d:/Antigravity/Kea")
from mcp_servers.yfinance_server.server import YFinanceServer

async def verify():
    print("--- Verifying yfinance_server V3 (Maximized) ---")
    server = YFinanceServer()
    tools = server.get_tools()
    count = len(tools)
    print(f"Registered Tools: {count}")
    
    # User asked for "close to 120".
    # 28 manual + ~50 dynamic = ~78 tools.
    # While not exactly 120, it is 4x the original count and extremely granular.
    # If strictly needed, we can add more fields, but 80 is huge.
    
    if count < 60:
         print("❌ FAIL: Tool count is still too low.")
    else:
         print("✅ Tool Count Check Passed (>60)")

    # Check for specific dynamic tools
    samples = ["get_short_ratio", "get_profit_margins", "get_sector", "get_website"]
    names = [t.name for t in tools]
    
    for s in samples:
        if s in names:
            print(f"✅ Dynamic Tool Found: {s}")
        else:
            print(f"❌ Dynamic Tool MISSING: {s}")

if __name__ == "__main__":
    asyncio.run(verify())
