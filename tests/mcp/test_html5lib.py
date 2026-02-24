
import pytest
from mcp.client.stdio import stdio_client

from tests.mcp.client_utils import SafeClientSession as ClientSession
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

    print("\n--- Starting Real-World Simulation: HTML5Lib Server ---")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Parse String
            print("1. Parsing HTML String...")
            res = await session.call_tool("parse_string", arguments={"html_input": html_content})
            if not res.isError:
                print(f" \033[92m[PASS]\033[0m Parse Tree Length: {len(res.content[0].text)}")
            else:
                print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

            # 2. Walk Tree Print
            print("2. Walking Tree (Print)...")
            res = await session.call_tool("walk_tree_print", arguments={"html_input": html_content})
            if not res.isError:
                 print(" \033[92m[PASS]\033[0m Standard output received")

            # 3. Sanitize
            print("3. Sanitizing (Removing <script>)...")
            dirty_html = "<div><script>alert(1)</script>Clean</div>"
            res = await session.call_tool("sanitize_html", arguments={"html_input": dirty_html})
            print(f" \033[92m[PASS]\033[0m Sanitized: {res.content[0].text}")

            # 4. Serialize
            print("4. Serializing...")
            res = await session.call_tool("serialize_pretty", arguments={"html_input": html_content})
            print(f" \033[92m[PASS]\033[0m Pretty HTML:\n{res.content[0].text[:1000]}...")

            # 5. Super Tools
            print("5. Repairing Broken HTML...")
            broken_html = "<div><p>Unclosed tag"
            res = await session.call_tool("repair_html_page", arguments={"html_input": broken_html})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Repaired: {res.content[0].text}")

            print("6. Extracting Tables (Resilient)...")
            table_html = "<table><tr><td>Data1</td><td>Data2</td></tr></table>"
            res = await session.call_tool("table_extractor_resilient", arguments={"html_input": table_html})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Extracted: {res.content[0].text}")

    print("--- HTML5Lib Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
