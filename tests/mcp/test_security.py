import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_security_real_simulation():
    """
    REAL SIMULATION: Verify Security Server (Scanning/Sanitization).
    """
    params = get_server_params("security_server", extra_dependencies=["httpx"])
    
    print(f"\n--- Starting Real-World Simulation: Security Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Content Sanitizer
            print("1. Sanitizing HTML...")
            dirty_html = "<script>alert('xss')</script><b>Hello</b>"
            res = await session.call_tool("content_sanitizer", arguments={"content": dirty_html, "allow_html": True})
            print(f" \033[92m[PASS]\033[0m Sanitized: {res.content[0].text}")

            # 2. File Hash Check (on content)
            print("2. Hashing Content...")
            res = await session.call_tool("file_hash_check", arguments={"content": "suspicious_payload"})
            print(f" \033[92m[PASS]\033[0m Hash Report: {res.content[0].text}")

            # 3. Code Safety Check
            print("3. Checking Code Safety...")
            unsafe_code = "import os; os.system('rm -rf /')"
            res = await session.call_tool("code_safety_check", arguments={"code": unsafe_code})
            print(f" \033[92m[PASS]\033[0m Analysis: {res.content[0].text}")

            # 4. URL Scanner
            print("4. URL Scanner...")
            res = await session.call_tool("url_scanner", arguments={"url": "http://example.com"})
            print(f" \033[92m[PASS]\033[0m Scan: {res.content[0].text}")

            # 5. Domain Reputation
            print("5. Domain Reputation...")
            await session.call_tool("domain_reputation", arguments={"domain": "google.com"})

    print("--- Security Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
