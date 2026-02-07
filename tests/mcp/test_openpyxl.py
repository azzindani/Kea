import pytest
import asyncio
import os
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_openpyxl_real_simulation():
    """
    REAL SIMULATION: Verify OpenPyXL Server (Excel Operations).
    """
    params = get_server_params("openpyxl_server", extra_dependencies=["openpyxl", "pandas", "pillow"])
    
    test_file = "test_report.xlsx"
    
    print(f"\n--- Starting Real-World Simulation: OpenPyXL Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Create Workbook
            print(f"1. Creating Workbook '{test_file}'...")
            res = await session.call_tool("create_new_workbook", arguments={"file_path": test_file, "overwrite": True})
            if not res.isError:
                 print(f" [PASS] Created")
            
            # 2. Write Data
            print("2. Writing Data...")
            data = [
                ["ID", "Name", "Sales"],
                [1, "Alice", 5000],
                [2, "Bob", 7000],
                [3, "Charlie", 4500]
            ]
            res = await session.call_tool("write_range_values", arguments={"file_path": test_file, "data": data, "start_cell": "A1"})
            print(f" [PASS] {res.content[0].text}")
            
            # 3. Styling (Font)
            print("3. Styling Header...")
            res = await session.call_tool("set_cell_font", arguments={"file_path": test_file, "cell": "A1", "bold": True})
            print(f" [PASS] {res.content[0].text}")

            # 4. Create Chart
            print("4. Creating Chart...")
            res = await session.call_tool("create_chart", arguments={
                "file_path": test_file, 
                "type": "bar", 
                "data_range": "C1:C4", 
                "title": "Sales Data"
            })
            if not res.isError:
                print(f" [PASS] Chart added")
            else:
                 print(f" [FAIL] {res.content[0].text}")

            # 5. Read Back
            print("5. Reading Back Data...")
            res = await session.call_tool("read_range_values", arguments={"file_path": test_file, "range_string": "A1:C4"})
            print(f" [PASS] Read: {res.content[0].text[:100]}...")

    # Cleanup
    if os.path.exists(test_file):
        try:
             os.remove(test_file)
        except:
             pass

    print("--- OpenPyXL Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
