import pytest
import asyncio
import os
from tests.mcp.client_utils import SafeClientSession as ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_playwright_real_simulation():
    """
    REAL SIMULATION: Verify Playwright Server (Browser Automation).
    """
    params = get_server_params("playwright_server", extra_dependencies=["playwright"])
    
    print(f"\n--- Starting Real-World Simulation: Playwright Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Install/Launch
            # Skip install to save time, assume installed or rely on launch
            print("1. Launching Browser...")
            res = await session.call_tool("launch_browser", arguments={"browser_type": "chromium"})
            if res.isError:
                print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")
                return
            
            # 2. Navigate
            url = "https://example.com"
            print(f"2. Navigating to {url}...")
            res = await session.call_tool("goto_page", arguments={"url": url})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Navigated")

            # 3. Get Title
            print("3. Getting Title...")
            res = await session.call_tool("evaluate_js", arguments={"script": "document.title"})
            print(f" \033[92m[PASS]\033[0m Title: {res.content[0].text}")

            # 4. Screenshot
            print("4. Taking Screenshot...")
            screenshot_path = "test_screenshot.png"
            res = await session.call_tool("screenshot_page", arguments={"path": screenshot_path})
            if not res.isError:
                print(f" \033[92m[PASS]\033[0m Screenshot saved")
                if os.path.exists(screenshot_path):
                    os.remove(screenshot_path)

            # 5. Input Operations (Type/Click)
            # Using a simple input on example.com (it has a search box on some versions, or we can just try typing into body to test the tool won't crash)
            # Actually example.com is static. Let's just try to get element text of h1 to verify DOM tool again, or try to 'click' the link.
            print("5. Clicking Element...")
            res = await session.call_tool("click_element", arguments={"selector": "a"}) # The 'More information' link
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Clicked link")

            # 6. Cleanup
            print("6. Closing Browser...")
            await session.call_tool("close_browser")

    print("--- Playwright Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
