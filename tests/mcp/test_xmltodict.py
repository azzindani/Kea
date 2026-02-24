
import pytest
from mcp import ClientSession
from mcp.client.stdio import stdio_client

from tests.mcp.client_utils import get_server_params


@pytest.mark.asyncio
async def test_xmltodict_real_simulation():
    """
    REAL SIMULATION: Verify XmlToDict Server.
    """
    params = get_server_params("xmltodict_server", extra_dependencies=["xmltodict"])

    xml_str = """<root><person><name>John</name><age>30</age></person></root>"""

    print("\n--- Starting Real-World Simulation: XmlToDict Server ---")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Parse XML String
            print(f"1. Parsing XML: '{xml_str}'...")
            res = await session.call_tool("parse_xml_string", arguments={"xml_input": xml_str})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Parsed Dict: {res.content[0].text}")

            # 2. Unparse Dict (Dict to XML)
            print("2. Unparsing Dict to XML...")
            data = {"root": {"status": "ok", "value": "100"}}
            res = await session.call_tool("unparse_dict_string", arguments={"data": data})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m XML Output: {res.content[0].text}")

            # 3. Valid Tool Call (Unparse Pretty)
            print("3. Unparsing Dict (Pretty)...")
            data = {"root": {"status": "ok", "value": "100"}}
            res = await session.call_tool("unparse_dict_pretty", arguments={"data": data})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m XML Output: {res.content[0].text}")

    print("--- XmlToDict Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
