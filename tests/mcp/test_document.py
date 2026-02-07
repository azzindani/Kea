import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_document_real_simulation():
    """
    REAL SIMULATION: Verify Document Server (PDF, Docx, HTML Parsing).
    """
    params = get_server_params("document_server", extra_dependencies=["httpx", "pymupdf", "python-docx", "pandas", "beautifulsoup4"])
    
    print(f"\n--- Starting Real-World Simulation: Document Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. HTML Parser (Wikipedia)
            print("1. HTML Parser (Wikipedia - Python)...")
            url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
            res = await session.call_tool("html_parser", arguments={"url": url, "extract": "text", "selector": "h1"})
            if not res.isError:
                print(f" [PASS] HTML H1: {res.content[0].text}")
            else:
                print(f" [FAIL] {res.content[0].text}")

            # 2. PDF Parser (Public PDF)
            print("2. PDF Parser (W3C HTTP Spec)...")
            pdf_url = "https://www.w3.org/Protocols/rfc2616/rfc2616.pdf"
            # Limit pages to 1 to avoid huge download/parse
            res = await session.call_tool("pdf_parser", arguments={"url": pdf_url, "pages": "1"})
            if not res.isError:
                print(f" [PASS] PDF Content: {res.content[0].text[:100]}...")
            else:
                 print(f" [FAIL] {res.content[0].text}")

            # 3. JSON Parser (Public JSON)
            print("3. JSON Parser (Sort of)...")
            json_url = "https://jsonplaceholder.typicode.com/todos/1"
            res = await session.call_tool("json_parser", arguments={"url": json_url})
            if not res.isError:
                print(f" [PASS] JSON Content: {res.content[0].text}")
            else:
                print(f" [FAIL] {res.content[0].text}")

    print("--- Document Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
