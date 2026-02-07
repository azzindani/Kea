import pytest
import asyncio
import os
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_shutil_real_simulation():
    """
    REAL SIMULATION: Verify Shutil Server (File Operations).
    """
    params = get_server_params("shutil_server", extra_dependencies=["pandas"])
    
    test_dir = "test_shutil_env"
    test_file = f"{test_dir}/test.txt"
    copy_file = f"{test_dir}/copy.txt"
    
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    
    print(f"\n--- Starting Real-World Simulation: Shutil Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Valid Path
            print("1. Validating Path...")
            res = await session.call_tool("validate_path", arguments={"path": os.getcwd()})
            print(f" [PASS] Valid: {res.content[0].text}")

            # 2. Touch File
            print(f"2. Creating file '{test_file}'...")
            res = await session.call_tool("touch_file", arguments={"path": os.path.abspath(test_file)})
            print(f" [PASS] Touched: {res.content[0].text}")

            # 3. Copy File
            print(f"3. Copying to '{copy_file}'...")
            res = await session.call_tool("copy_file", arguments={"src": os.path.abspath(test_file), "dst": os.path.abspath(copy_file)})
            print(f" [PASS] Copied: {res.content[0].text}")
            
            # 4. Get Disk Usage
            print("4. Checking Disk Usage...")
            res = await session.call_tool("get_disk_usage", arguments={"path": "."})
            print(f" [PASS] Usage: {res.content[0].text}")

    # Cleanup
    import shutil
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    print("--- Shutil Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
