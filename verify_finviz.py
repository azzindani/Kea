
import sys
import os
import asyncio
from typing import Any

# Add project root to path
sys.path.insert(0, r"d:\Antigravity\Kea")

from mcp_servers.finviz_server.tools import screener
from shared.mcp.protocol import ToolResult, JSONContent, TextContent

async def test_finviz():
    print("Testing Finviz Screener...")
    try:
        # Call the function directly (bypassing FastMCP server wrapper for unit test)
        # Using a signal that might have data, or handled gracefully
        # 'top_gainers' usually has data. Limit 5 to be fast.
        result = await screener.get_screener_signal(limit=5, signal="top_gainers")
        
        if isinstance(result, ToolResult):
            print("✅ Result is ToolResult")
            
            has_text = any(isinstance(c, TextContent) for c in result.content)
            has_json = any(isinstance(c, JSONContent) for c in result.content)
            
            if has_text:
                print("✅ Has TextContent")
            else:
                print("❌ Missing TextContent")
                
            if has_json:
                print("✅ Has JSONContent")
                # Inspect JSON data
                json_content = next(c for c in result.content if isinstance(c, JSONContent))
                data = json_content.data
                print(f"   Data type: {type(data)}")
                if isinstance(data, list) and len(data) > 0:
                    print(f"   Sample row: {data[0].keys()}")
            else:
                print("❌ Missing JSONContent")
                
        else:
            print(f"❌ Result is NOT ToolResult: {type(result)}")
            print(result)

    except Exception as e:
        print(f"❌ Verification failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_finviz())
