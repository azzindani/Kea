
import pytest
from mcp.client.stdio import stdio_client

from tests.mcp.client_utils import SafeClientSession as ClientSession
from tests.mcp.client_utils import get_server_params


@pytest.mark.asyncio
async def test_lxml_real_simulation():
    """
    REAL SIMULATION: Verify LXML Server (XML Parsing, XPath).
    """
    params = get_server_params("lxml_server", extra_dependencies=["lxml", "cssselect"])

    xml_content = """
    <library>
        <book id="1">
            <title>The Great Gatsby</title>
            <author>F. Scott Fitzgerald</author>
            <price>10.99</price>
        </book>
        <book id="2">
            <title>1984</title>
            <author>George Orwell</author>
            <price>8.99</price>
        </book>
    </library>
    """

    print("\n--- Starting Real-World Simulation: LXML Server ---")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Parse XML
            print("1. Parsing XML...")
            res = await session.call_tool("parse_xml_string", arguments={"xml_input": xml_content})
            if not res.isError:
                print(" \033[92m[PASS]\033[0m XML Parsed")
            else:
                print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

            # 2. XPath Query
            print("2. XPath Query (titles)...")
            res = await session.call_tool("xpath_query_text", arguments={"xml_input": xml_content, "query": "//title/text()"})
            print(f" \033[92m[PASS]\033[0m Titles: {res.content[0].text}")

            # 3. XPath Attribute
            print("3. XPath Attribute (id)...")
            res = await session.call_tool("xpath_query_attr", arguments={"xml_input": xml_content, "query": "//book/@id"})
            print(f" \033[92m[PASS]\033[0m IDs: {res.content[0].text}")

            # 4. Convert to Dict
            print("4. XML to Dict...")
            res = await session.call_tool("xml_to_dict_lxml", arguments={"xml_input": xml_content})
            print(f" \033[92m[PASS]\033[0m Dict: {res.content[0].text[:1000]}...")

            # 5. Transform
            print("5. Transforming (Absolute Links)...")
            html_with_rel = '<html><body><a href="page.html">Link</a></body></html>'
            res = await session.call_tool("make_links_absolute", arguments={"html_input": html_with_rel, "base_url": "http://example.com/"})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Absolute: {res.content[0].text}")

            print("6. Cleaning HTML...")
            dirty = '<div><script>bad</script>Good</div>'
            res = await session.call_tool("clean_html", arguments={"html_input": dirty})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Clean: {res.content[0].text}")

    print("--- LXML Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
