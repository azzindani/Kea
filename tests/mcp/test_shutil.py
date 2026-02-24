import os

import pytest
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

    print("\n--- Starting Real-World Simulation: Shutil Server ---")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Valid Path
            print("1. Validating Path...")
            res = await session.call_tool("validate_path", arguments={"path": os.getcwd()})
            print(f" \033[92m[PASS]\033[0m Valid: {res.content[0].text}")

            # 2. Touch File
            print(f"2. Creating file '{test_file}'...")
            res = await session.call_tool("touch_file", arguments={"path": os.path.abspath(test_file)})
            print(f" \033[92m[PASS]\033[0m Touched: {res.content[0].text}")

            # 3. Copy File
            print(f"3. Copying to '{copy_file}'...")
            res = await session.call_tool("copy_file", arguments={"src": os.path.abspath(test_file), "dst": os.path.abspath(copy_file)})
            print(f" \033[92m[PASS]\033[0m Copied: {res.content[0].text}")

            # 4. Get Disk Usage
            print("4. Checking Disk Usage...")
            res = await session.call_tool("get_disk_usage", arguments={"path": "."})
            print(f" \033[92m[PASS]\033[0m Usage: {res.content[0].text}")

            # 5. Archive
            print("5. Archiving...")
            # Create a dummy dir to archive
            dummy_dir = f"{test_dir}/archive_me"
            if not os.path.exists(dummy_dir): os.makedirs(dummy_dir)
            with open(f"{dummy_dir}/f1.txt", "w") as f: f.write("content")

            await session.call_tool("make_archive", arguments={"base_name": f"{test_dir}/my_archive", "format": "zip", "root_dir": dummy_dir})

            # 6. Bulk Copy
            print("6. Bulk Copy...")
            bulk_dest = f"{test_dir}/bulk_dest"
            if not os.path.exists(bulk_dest): os.makedirs(bulk_dest)
            await session.call_tool("bulk_copy_files", arguments={"files": [f"{dummy_dir}/f1.txt"], "destination_dir": bulk_dest})

            # 7. Super Tools
            print("7. Super Tools (Organize)...")
            await session.call_tool("organize_by_extension", arguments={"directory": bulk_dest})

    # Cleanup
    import shutil
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    print("--- Shutil Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
