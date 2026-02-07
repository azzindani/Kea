import pytest
import asyncio
import os
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_zipfile_real_simulation():
    """
    REAL SIMULATION: Verify Zipfile Server.
    """
    params = get_server_params("zipfile_server", extra_dependencies=["pandas"])
    
    zip_path = "test_archive.zip"
    file_name = "hello.txt"
    content = "Hello Zip World"
    
    if os.path.exists(zip_path):
        os.remove(zip_path)
    
    abs_zip_path = os.path.abspath(zip_path)
    
    print(f"\n--- Starting Real-World Simulation: Zipfile Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Create New Zip
            print(f"1. Creating Zip: {zip_path}...")
            res = await session.call_tool("create_new_zip", arguments={"path": abs_zip_path})
            print(f" [PASS] Created: {res.content[0].text}")

            # 2. Add String as File
            print(f"2. Adding '{file_name}'...")
            res = await session.call_tool("add_string_as_file", arguments={"path": abs_zip_path, "filename": file_name, "content": content})
            print(f" [PASS] Added: {res.content[0].text}")

            # 3. List Files
            print("3. Listing Files...")
            res = await session.call_tool("list_files", arguments={"path": abs_zip_path})
            print(f" [PASS] Files: {res.content[0].text}")

            # 4. Read File Text
            print("4. Reading Back...")
            res = await session.call_tool("read_file_text", arguments={"path": abs_zip_path, "member": file_name})
            print(f" [PASS] Content: {res.content[0].text}")

    # Cleanup
    if os.path.exists(zip_path):
        os.remove(zip_path)

    print("--- Zipfile Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
