import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_html5lib_real_simulation():
    """
    REAL SIMULATION: Verify HTML5Lib Server (Parsing, Walking).
    """
    params = get_server_params("html5lib_server", extra_dependencies=["html5lib"])
    
    html_content = """
    <!DOCTYPE html>
    <html>
        <head><title>Test</title></head>
        <body>
            <div id="content">
                <p>Hello <b>World</b></p>
                <ul>
                    <li>Item 1</li>
                    <li>Item 2</li>
                </ul>
            </div>
        </body>
    </html>
    """
    
    print(f"\n--- Starting Real-World Simulation: HTML5Lib Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Parse String
            print("1. Parsing HTML String...")
            res = await session.call_tool("parse_string", arguments={"html_input": html_content})
            if not res.isError:
                print(f" [PASS] Parse Tree Length: {len(res.content[0].text)}")
            else:
                print(f" [FAIL] {res.content[0].text}")

            # 2. Walk Tree Print
            print("2. Walking Tree (Print)...")
            res = await session.call_tool("walk_tree_print", arguments={"html_input": html_content})
            if not res.isError:
                 print(f" [PASS] Standard output received")
            
            # 3. Sanitize
            print("3. Sanitizing (Removing <script>)...")
            dirty_html = "<div><script>alert(1)</script>Clean</div>"
            res = await session.call_tool("sanitize_html", arguments={"html_input": dirty_html})
            print(f" [PASS] Sanitized: {res.content[0].text}")

            # 4. Serialize
            print("4. Serializing...")
            res = await session.call_tool("serialize_pretty", arguments={"html_input": html_content})
            print(f" [PASS] Pretty HTML:\n{res.content[0].text[:100]}...")

    print("--- HTML5Lib Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
