
import asyncio
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from services.mcp_host.core.session_registry import SessionRegistry

async def test_yfinance():
    print("🚀 Starting yfinance verification...")
    registry = SessionRegistry()
    
    try:
        session = await registry.get_session("yfinance_server")
        print("✅ Session spawned successfully")
        
        tools = await session.list_tools()
        print(f"✅ Discovered {len(tools)} tools")
        
        if not tools:
            print("❌ No tools discovered!")
            return

        # Test a simple tool
        print("🔍 Testing get_current_price for AAPL...")
        result = await session.call_tool("get_current_price", {"ticker": "AAPL"})
        
        print(f"✅ Result content type: {type(result.content)}")
        if result.content and hasattr(result.content[0], 'text'):
             print(f"✅ Result text: {result.content[0].text[:100]}...")
        else:
             print(f"✅ Result: {result}")
        
    except Exception as e:
        print(f"❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await registry.shutdown()

if __name__ == "__main__":
    asyncio.run(test_yfinance())
