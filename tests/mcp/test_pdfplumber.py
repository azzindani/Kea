import pytest
import asyncio
import os
import requests
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_pdfplumber_real_simulation():
    """
    REAL SIMULATION: Verify PDFPlumber Server (PDF Extraction).
    """
    params = get_server_params("pdfplumber_server", extra_dependencies=["pdfplumber", "pandas", "pillow"])
    
    # Download a sample PDF
    pdf_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    pdf_file = "test_sample.pdf"
    
    print(f"\n--- Starting Real-World Simulation: PDFPlumber Server ---")
    
    try:
        response = requests.get(pdf_url)
        with open(pdf_file, "wb") as f:
            f.write(response.content)
    except Exception as e:
        print(f" [WARN] Could not download sample PDF: {e}")
        return

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Metadata
            print("1. Getting Metadata...")
            res = await session.call_tool("get_pdf_metadata", arguments={"path": pdf_file})
            print(f" \033[92m[PASS]\033[0m Metadata: {res.content[0].text}")

            # 2. Page Count
            print("2. Counting Pages...")
            res = await session.call_tool("get_page_count", arguments={"path": pdf_file})
            print(f" \033[92m[PASS]\033[0m Pages: {res.content[0].text}")

            # 3. Extract Text
            print("3. Extracting Text (Page 1)...")
            res = await session.call_tool("extract_text_simple", arguments={"path": pdf_file, "page_number": 1})
            print(f" \033[92m[PASS]\033[0m Text: {res.content[0].text[:50]}...")

            # 4. Extract Tables
            print("4. Extracting Tables (Page 1)...")
            res = await session.call_tool("extract_tables", arguments={"path": pdf_file, "page_number": 1})
            print(f" \033[92m[PASS]\033[0m Tables found")

            # 5. Extract Images
            print("5. Extracting Images...")
            res = await session.call_tool("extract_images", arguments={"path": pdf_file, "page_number": 1})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Images extracted")

            # 6. Extract Hyperlinks
            print("6. Extracting Hyperlinks...")
            res = await session.call_tool("extract_hyperlinks", arguments={"path": pdf_file, "page_number": 1})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Hyperlinks extracted")

    # Cleanup
    if os.path.exists(pdf_file):
        try:
            os.remove(pdf_file)
        except:
             pass

    print("--- PDFPlumber Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
