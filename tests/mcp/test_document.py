import pytest
from mcp.client.stdio import stdio_client

from tests.mcp.client_utils import SafeClientSession as ClientSession
from tests.mcp.client_utils import get_server_params


@pytest.mark.asyncio
async def test_document_real_simulation():
    """
    REAL SIMULATION: Verify Document Server (PDF, Docx, HTML Parsing).
    """
    params = get_server_params("document_server", extra_dependencies=["httpx", "pymupdf", "python-docx", "pandas", "beautifulsoup4"])

    print("\n--- Starting Real-World Simulation: Document Server ---")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. HTML Parser (Wikipedia)
            print("1. HTML Parser (Wikipedia - Python)...")
            url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
            res = await session.call_tool("html_parser", arguments={"url": url, "extract": "text", "selector": "h1"})
            if not res.isError:
                print(f" \033[92m[PASS]\033[0m HTML H1: {res.content[0].text}")
            else:
                print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

            # 2. PDF Parser (Public PDF)
            print("2. PDF Parser (W3C HTTP Spec)...")
            pdf_url = "https://www.w3.org/Protocols/rfc2616/rfc2616.pdf"
            # Limit pages to 1 to avoid huge download/parse
            res = await session.call_tool("pdf_parser", arguments={"url": pdf_url, "pages": "1"})
            if not res.isError:
                print(f" \033[92m[PASS]\033[0m PDF Content: {res.content[0].text[:1000]}...")
            else:
                print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

            # 3. JSON Parser (Public JSON)
            print("3. JSON Parser (Sort of)...")
            json_url = "https://jsonplaceholder.typicode.com/todos/1"
            res = await session.call_tool("json_parser", arguments={"url": json_url})
            if not res.isError:
                print(f" \033[92m[PASS]\033[0m JSON Content: {res.content[0].text}")
            else:
                print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

            # 4. Docx Parser
            print("4. Docx Parser (Create dummy)...")
            import os

            # Use absolute path to ensure server can find it
            cwd = os.getcwd()
            docx_path = os.path.join(cwd, "test_doc_parser.docx")
            xlsx_path = os.path.join(cwd, "test_doc_parser.xlsx")

            # Attempt to create dummy files locally
            try:
                import docx
                doc = docx.Document()
                doc.add_paragraph("Hello from Document Server Test")
                doc.save(docx_path)
                print(" \033[92m[INFO]\033[0m Local docx created.")
            except ImportError:
                print(" \033[93m[INFO]\033[0m Test environment lacks python-docx, skipping local file creation.")

            if os.path.exists(docx_path):
                res = await session.call_tool("docx_parser", arguments={"url": docx_path})
                if not res.isError:
                    print(f" \033[92m[PASS]\033[0m Docx Text: {res.content[0].text[:100]}...")
                else:
                    print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")
            else:
                print(" \033[93m[SKIP]\033[0m Docx file not found, skipping tool test.")

            # 5. Xlsx Parser
            print("5. Xlsx Parser (Create dummy)...")
            try:
                import pandas as pd
                df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
                df.to_excel(xlsx_path, index=False)
                print(" \033[92m[INFO]\033[0m Local xlsx created.")
            except ImportError:
                print(" \033[93m[INFO]\033[0m Test environment lacks pandas/openpyxl, skipping local file creation.")

            if os.path.exists(xlsx_path):
                res = await session.call_tool("xlsx_parser", arguments={"url": xlsx_path})
                if not res.isError:
                    print(f" \033[92m[PASS]\033[0m Xlsx Content: {res.content[0].text[:100]}...")
                else:
                    print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")
            else:
                print(" \033[93m[SKIP]\033[0m Xlsx file not found, skipping tool test.")

            # Cleanup
            if os.path.exists(docx_path): os.remove(docx_path)
            if os.path.exists(xlsx_path): os.remove(xlsx_path)

    print("--- Document Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
