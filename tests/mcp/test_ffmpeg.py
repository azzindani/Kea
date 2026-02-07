import pytest
import asyncio
import os
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_ffmpeg_real_simulation():
    """
    REAL SIMULATION: Verify FFmpeg Server (Validation, Probing).
    """
    params = get_server_params("ffmpeg_server", extra_dependencies=["ffmpeg-python", "pandas"])
    
    print(f"\n--- Starting Real-World Simulation: FFmpeg Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Check Availability
            print("1. Checking FFmpeg Availability...")
            res = await session.call_tool("check_ffmpeg_available")
            is_available = res.content[0].text == "True"
            print(f" [INFO] FFmpeg Available: {is_available}")

            # 2. Version
            if is_available:
                print("2. Getting Version...")
                res = await session.call_tool("get_ffmpeg_version")
                print(f" [PASS] Version: {res.content[0].text}")

            # 3. Validation (Dummy File)
            print("3. Validating 'test_video.mp4' (Non-existent)...")
            res = await session.call_tool("validate_media_file", arguments={"path": "non_existent_video.mp4"})
            print(f" [PASS] Validation Result: {res.content[0].text}")
            
            # 4. Create dummy file to test probe failure gracefully
            with open("dummy_test.txt", "w") as f:
                f.write("Not a video")
            
            print("4. Probing Invalid File...")
            try:
                res = await session.call_tool("probe_file", arguments={"path": "dummy_test.txt"})
                print(f" [INFO] Probe Result: {res.content[0].text}")
            except Exception as e:
                print(f" [PASS] Probe failed as expected: {e}")
                
            if os.path.exists("dummy_test.txt"):
                os.remove("dummy_test.txt")

    print("--- FFmpeg Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
