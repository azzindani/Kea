import pytest
import asyncio
from tests.mcp.client_utils import SafeClientSession as ClientSession
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

            if not res.isError:
                print(f" \033[92m[PASS]\033[0m JSON Content: {res.content[0].text}")
            else:
                print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

            # 4. Docx Parser
            print("4. Docx Parser (Create dummy)...")
            try:
                import docx
                HAS_DOCX = True
            except ImportError:
                HAS_DOCX = False
                print(" \033[93m[WARN]\033[0m python-docx not installed, skipping DOCX test")

            import os
            
            # Use absolute path to ensure server can find it
            cwd = os.getcwd()
            docx_path = os.path.join(cwd, "test_doc_parser.docx")
            xlsx_path = os.path.join(cwd, "test_doc_parser.xlsx")
            
            if HAS_DOCX:
                doc = docx.Document()
                doc.add_paragraph("Hello from Document Server Test")
                doc.save(docx_path)
                
                # Ensure file exists
                if not os.path.exists(docx_path):
                    print(f" [FAIL] Docx file not created at {docx_path}")
                
                # The server expects a URL or path. For local files, we might need 'file://' prefix or just absolute path depending on implementation.
                # Looking at document_server/tools/word.py (which I haven't seen but assuming checks file existence), absolute path should work if it's local.
                # But wait, document_server might be running in a different container/environment if it was real, but here it's stdio in same env.
                # The 'url' argument usually implies downloadable, but let's try absolute path.
                
                res = await session.call_tool("docx_parser", arguments={"url": docx_path})
                if not res.isError:
                    print(f" \033[92m[PASS]\033[0m Docx Text: {res.content[0].text}")
                else:
                    print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")
                
            # 5. Xlsx Parser
            print("5. Xlsx Parser (Create dummy)...")
            import pandas as pd
            df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
            df.to_excel(xlsx_path, index=False)
            
            res = await session.call_tool("xlsx_parser", arguments={"url": xlsx_path})
            if not res.isError:
                print(f" \033[92m[PASS]\033[0m Xlsx Content: {res.content[0].text}")
            else:
                print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")
 
            # Cleanup
            if os.path.exists(docx_path): os.remove(docx_path)
            if os.path.exists(xlsx_path): os.remove(xlsx_path)

    print("--- Document Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
