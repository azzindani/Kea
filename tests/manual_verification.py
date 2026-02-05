
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.getcwd())

from shared.logging import setup_logging, LogConfig
setup_logging(LogConfig(level="DEBUG"))
from shared.logging import get_logger

logger = get_logger("manual_verification")

async def verify_registry():
    logger.info("--- Starting Manual Verification ---")
    
    # 1. Import Registry
    try:
        from services.mcp_host.core.session_registry import get_session_registry
        registry = get_session_registry()
        logger.info("✅ SessionRegistry imported successfully")
    except Exception as e:
        logger.error(f"❌ Failed to import SessionRegistry: {e}")
        return

    # 2. Skip Global Discovery (Too Slow/Fragile)
    logger.info("⏩ Skipping global discovery (Targeted Verification)")
    
    # 3. Execute 'get_idx_tickers' (Triggers Spawning)
    try:
        logger.info("🚀 Spawning 'finance_server' explicitly...")
        
        # Ensure registry has scanned folders (it should do this on init or access)
        # We access internal map to check
        if "finance_server" not in registry.server_configs:
            # Trigger discovery if needed (local scan only, no spawning)
            logger.info("Triggering local scan...")
            registry._discover_local_servers()
            
        if "finance_server" not in registry.server_configs:
             logger.error("❌ 'finance_server' not found in configs")
             return

        # Get Session
        session = await registry.get_session("finance_server")
        logger.info("✅ Connected to finance_server")
        
        # Execute (Force Refresh for Intelligence Test)
        result = await session.call_tool("get_idx_tickers", {"index_name": "LQ45", "force_refresh": True})
        
        # Parse Result
        content = result.content[0].text
        logger.info("✅ 'get_idx_tickers' Execution Successful!")
        print("\n--- Finance Output ---")
        print(content)
        print("----------------------\n")
        
    except Exception as e:
        logger.error(f"❌ Finance Execution failed: {e}")

    # 4. Verify Scraper (Targeted)
    try:
        logger.info("🚀 Spawning 'scraper_server' explicitly...")
        session = await registry.get_session("scraper_server")
        logger.info("✅ Connected to scraper_server")
        
        # Just check connection, avoiding full scrape to save time unless necessary
        # Or list specific tools from this server
        tools = await session.list_tools()
        tool_names = [t.name for t in tools.tools]
        logger.info(f"Scraper Tools: {tool_names}")
        
        if "browser_scrape" in tool_names:
            logger.info("✅ 'browser_scrape' Found on server")
            
    except Exception as e:
        logger.error(f"❌ Scraper Verification failed: {e}")
        
    # 5. Cleanup
    await registry.shutdown()
    logger.info("✅ Shutdown complete")

if __name__ == "__main__":
    asyncio.run(verify_registry())
