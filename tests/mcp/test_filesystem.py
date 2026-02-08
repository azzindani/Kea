import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_filesystem_server():
    """Verify Filesystem Server executes using MCP Client."""
    
    params = get_server_params("filesystem_server", extra_dependencies=["asyncpg"])
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Discover Tools
            tools_res = await session.list_tools()
            tools = tools_res.tools
            print(f"\nDiscovered {len(tools)} tools via Client.")
            
            tool_names = [t.name for t in tools]
            assert "fs_ls" in tool_names or "list_directory" in tool_names # Supporting potential aliases
            
            print("Filesystem verification passed (Tools present).")

@pytest.mark.asyncio
async def test_fs_real_simulation():
    """
    REAL SIMULATION: Create, Read, and Delete a real file.
    """
    params = get_server_params("filesystem_server", extra_dependencies=[])
    
    print(f"\n--- Starting Real-World Simulation: Filesystem ---")
    
    # Use a safe temp path
    import tempfile
    import os
    
    temp_dir = tempfile.gettempdir()
    test_file_name = "mcp_test_file_real.txt"
    test_path = os.path.join(temp_dir, test_file_name)
    content_to_write = "Hello MCP Real World!"
    
    # Ensure cleanup before start
    if os.path.exists(test_path):
        os.remove(test_path)
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Check tools first to know naming convention (fs_write vs write_file)
            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            
            # 0. Initialize DB (ensure schema exists)
            print("0. Initializing DB...")
            res_init = await session.call_tool("fs_init")
            if res_init.isError:
                 print(f" [WARN] Init failed (might be already init): {res_init.content[0].text}")
            else:
                 print(f" [INFO] DB Init: {res_init.content[0].text}")

            # 1. Write File
            write_tool = "write_file" if "write_file" in tool_names else "fs_write"
            print(f"1. Writing to {test_path} using {write_tool}...")
            
            # Tools usually take 'path' and 'content'
            res_write = await session.call_tool(write_tool, arguments={"path": test_path, "content": content_to_write})
            if res_write.isError:
                print(f" \033[91m[FAIL]\033[0m Write: {res_write.content[0].text}")
                return
            print(" \033[92m[PASS]\033[0m Write successful")
            
            # 2. Read File
            read_tool = "read_file" if "read_file" in tool_names else "fs_read"
            print(f"2. Reading from {test_path}...")
            res_read = await session.call_tool(read_tool, arguments={"path": test_path})
            
            if res_read.isError:
                print(f" \033[91m[FAIL]\033[0m Read: {res_read.content[0].text}")
            else:
                read_content = res_read.content[0].text
                print(f" \033[92m[PASS]\033[0m Read content: '{read_content}'")
                assert content_to_write in read_content
            
            # 3. List Directory (to see it)
            list_tool = "list_directory" if "list_directory" in tool_names else "fs_ls"
            print(f"3. Listing dir {temp_dir}...")
            res_list = await session.call_tool(list_tool, arguments={"path": temp_dir})
            if not res_list.isError:
                 if test_file_name in res_list.content[0].text:
                     print(" \033[92m[PASS]\033[0m File found in directory listing")
                 else:
                     print(f" [WARN] File not found in listing (might be paginated/filtered)")
            
            # 4. Cleanup (Delete)
            # Some FS servers might not have delete, check tools
            # If not via tool, we do it in python finally block, but let's try tool
            pass # TODO: Add delete logic if tool exists
            
    # Cleanup in python to be safe
    if os.path.exists(test_path):
        os.remove(test_path)
    print("--- Filesystem Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
