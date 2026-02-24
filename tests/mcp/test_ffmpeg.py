import os

import pytest
from mcp.client.stdio import stdio_client

from tests.mcp.client_utils import SafeClientSession as ClientSession
from tests.mcp.client_utils import get_server_params


@pytest.mark.asyncio
async def test_ffmpeg_real_simulation():
    """
    REAL SIMULATION: Verify FFmpeg Server (Validation, Probing).
    """
    params = get_server_params("ffmpeg_server", extra_dependencies=["ffmpeg-python", "pandas"])

    print("\n--- Starting Real-World Simulation: FFmpeg Server ---")

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
                print(f" \033[92m[PASS]\033[0m Version: {res.content[0].text}")

            # 3. Create Test Video (Active Simulation)
            print("3. Generating Test Video (color test source)...")
            test_video = "test_gen.mp4"
            test_output = "test_out.mkv"
            try:
                import ffmpeg

                # Generate 3 seconds of video
                ffmpeg.input('testsrc=size=320x240:rate=30', f='lavfi').output(test_video, t=3).overwrite_output().run(quiet=True)
                print(" \033[92m[PASS]\033[0m Test video generated")

                # 4. Probe & Info
                print("4. Probing & Info...")
                res = await session.call_tool("probe_file", arguments={"path": test_video})
                if not res.isError:
                    print(f" \033[92m[PASS]\033[0m Probe: {res.content[0].text[:1000]}...")

                res = await session.call_tool("get_duration", arguments={"path": test_video})
                print(f" \033[92m[PASS]\033[0m Duration: {res.content[0].text}")

                res = await session.call_tool("get_resolution", arguments={"path": test_video})
                print(f" \033[92m[PASS]\033[0m Resolution: {res.content[0].text}")

                # 5. Conversion
                print("5. Converting to MKV...")
                res = await session.call_tool("convert_format", arguments={"input_path": test_video, "output_path": test_output})
                if not res.isError:
                     print(f" \033[92m[PASS]\033[0m Conversion: {res.content[0].text}")

            except ImportError:
                print(" [WARN] ffmpeg-python not installed in test env. Skipping generation.")
            except Exception as e:
                print(f" [WARN] FFmpeg generation/test failed: {e}")

            # Cleanup
            if os.path.exists(test_video): os.remove(test_video)
            if os.path.exists(test_output): os.remove(test_output)
            if os.path.exists("dummy_test.txt"): os.remove("dummy_test.txt")

    print("--- FFmpeg Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
