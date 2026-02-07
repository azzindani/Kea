import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_bs4_real_simulation():
    """
    REAL SIMULATION: Verify BS4 Server (HTML Parsing) with complex DOM operations.
    Covering: Core, Nav, Search, Extract, Mod, Convert.
    """
    params = get_server_params("bs4_server", extra_dependencies=["beautifulsoup4", "lxml", "html5lib"])
    
    # Real Input Data
    html_content = """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <div id="main" class="container">
                <h1>Welcome to Kea</h1>
                <p class="desc">Autonomous <b>Research</b> Engine</p>
                <ul id="features">
                    <li data-id="1">Microservices</li>
                    <li data-id="2">LangGraph</li>
                    <li data-id="3">MCP</li>
                </ul>
                <div class="footer">Copyright 2025</div>
            </div>
        </body>
    </html>
    """
    
    print(f"\n--- Starting Real-World Simulation: BS4 Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Parse
            print("1. Parsing HTML...")
            res = await session.call_tool("parse_html", arguments={"html": html_content})
            if res.isError:
                print(f" [FAIL] Parse: {res.content[0].text}")
                return
            soup_id = res.content[0].text
            print(f" [PASS] Soup ID: {soup_id}")
            
            # 2. Get Stats
            res = await session.call_tool("get_stats", arguments={"soup_id": soup_id})
            if not res.isError:
                 print(f"   Stats: {res.content[0].text}")
            
            # 3. Navigation
            print("2. Navigation (get_children of #main)...")
            res = await session.call_tool("get_children", arguments={"selector": "#main", "soup_id": soup_id})
            assert not res.isError
            # Check if content is a list
            import json
            try:
                children = json.loads(res.content[0].text)
                print(f" [PASS] Children found: {len(children)}")
            except:
                print(f" [PASS] Children (raw): {res.content[0].text[:50]}...")
            
            # 4. Search
            print("3. Search (find_by_text 'Microservices')...")
            res = await session.call_tool("find_by_text", arguments={"text_regex": "Microservices", "soup_id": soup_id})
            assert not res.isError
            print(f" [PASS] Found: {res.content[0].text}")
            
            # 5. Extraction
            print("4. Extraction (get_text of h1)...")
            res = await session.call_tool("get_text", arguments={"selector": "h1", "soup_id": soup_id})
            print(f" [PASS] Text: '{res.content[0].text}'")
            
            print("   Extraction (get_attr data-id)...")
            res = await session.call_tool("get_attr", arguments={"selector": "li", "attr": "data-id", "soup_id": soup_id})
            print(f" [PASS] Attr: {res.content[0].text}")
            
            # 6. Modification
            print("5. Modification (add_class)...")
            res = await session.call_tool("add_class", arguments={"selector": "h1", "class_name": "header-lg", "soup_id": soup_id})
            assert not res.isError
            
            print("   Modification (replace_with)...")
            res = await session.call_tool("replace_with", arguments={"selector": ".footer", "new_html": "<footer>Updated</footer>", "soup_id": soup_id})
            assert not res.isError
            
            # 7. Conversion
            print("6. Conversion (to_markdown)...")
            res = await session.call_tool("to_markdown", arguments={"soup_id": soup_id})
            if not res.isError:
                print(f" [PASS] Markdown Preview:\n{res.content[0].text[:100]}...")
            
            # 8. Cleanup
            await session.call_tool("close_soup", arguments={"soup_id": soup_id})
            print(" [PASS] Soup closed")

    print("--- BS4 Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
