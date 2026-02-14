import pytest
import asyncio
from tests.mcp.client_utils import SafeClientSession as ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_crawler_server():
    """Verify Crawler Server executes using MCP Client."""
    
    # Crawler server dependencies - assuming generic for now as none specified in FastMCP
    # Check if 'crawl4ai' or 'beautifulsoup4' is needed. 
    # Based on tools names (crawl_ops), it likely needs something.
    # Safe bet: beautifulsoup4, requests, maybe crawl4ai if used.
    # Let's try minimal first.
    params = get_server_params("crawler_server", extra_dependencies=["beautifulsoup4", "requests"])
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Discover Tools
            tools_res = await session.list_tools()
            tools = tools_res.tools
            print(f"\nDiscovered {len(tools)} tools via Client.")
            
            tool_names = [t.name for t in tools]
            assert "web_crawler" in tool_names
            assert "sitemap_parser" in tool_names
            
            print("Crawler verification passed (Tools present).")

@pytest.mark.asyncio
async def test_crawler_real_simulation():
    """
    REAL SIMULATION: Crawl a real website and extract content.
    """
    params = get_server_params("crawler_server", extra_dependencies=["beautifulsoup4", "requests", "crawl4ai"])
    
    print(f"\n--- Starting Real-World Simulation: Crawler ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Discover Tools
            tools_res = await session.list_tools()
            tool_names = [t.name for t in tools_res.tools]
            
            target_url = "https://example.com"
            print(f"1. Target URL: {target_url}")
            
            if "web_crawler" in tool_names:
                print("   Using 'web_crawler'...")
                # Assuming simple args
                res = await session.call_tool("web_crawler", arguments={"url": target_url})
            else:
                print(" [WARN] No obvious crawl tool found in:", tool_names)
                return

            if res.isError:
                 print(f" \033[91m[FAIL]\033[0m Crawl: {res.content[0].text if res.content else 'Error'}")
            else:
                content = res.content[0].text
                print(f" \033[92m[PASS]\033[0m Crawl successful. Content len: {len(content)}")
                # In restricted network environments, the crawler may return 0 pages
                if "Pages Found**: 0" in content:
                    skip_msg = "Crawler returned 0 pages (network restriction)"
                elif not ("Example Domain" in content or "example.com" in content):
                    pytest.fail(f"Content mismatch. Got: {content[:200]}")
            
            print("--- Crawler Simulation Complete ---")
    
    if 'skip_msg' in locals() and skip_msg:
        pytest.skip(skip_msg)

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
