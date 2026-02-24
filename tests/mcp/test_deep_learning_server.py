
import pytest
from mcp.client.stdio import stdio_client

from tests.mcp.client_utils import SafeClientSession as ClientSession
from tests.mcp.client_utils import get_server_params


@pytest.mark.asyncio
async def test_deep_learning_server(tmp_path):
    """
    Verify Deep Learning Tools: Layers, Optimizers, Components, Applications.
    """
    params = get_server_params("deep_learning_server", extra_dependencies=["tensorflow", "pandas", "numpy", "scikit-learn", "structlog"])

    print("\n--- Starting DL Server Simulation ---")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # --- Previous Tests (Brief) ---
            await session.call_tool("add_dense", arguments={"units": 32})

            # --- New Tests ---

            # 4. Components
            print("4. Testing Components (Loss/Metric/Init)...")

            # Loss
            res = await session.call_tool("loss_categorical_crossentropy", arguments={"from_logits": True})
            assert not res.isError
            print(f" \033[92m[PASS]\033[0m Loss: {res.content[0].text}")

            # Metric
            res = await session.call_tool("metric_auc", arguments={"curve": "ROC"})
            assert not res.isError
            print(f" \033[92m[PASS]\033[0m Metric: {res.content[0].text}")

            # Init
            res = await session.call_tool("init_he_uniform", arguments={})
            assert not res.isError
            print(f" \033[92m[PASS]\033[0m Init: {res.content[0].text}")

            # 5. Applications
            print("5. Testing Applications (Pretrained)...")
            res = await session.call_tool("app_mobilenet", arguments={"input_shape": [128, 128, 3], "include_top": False})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m MobileNet: {res.content[0].text[:100]}...")
            else:
                 print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

            # 6. Advanced Data Ops
            print("6. Testing Sequence Padding...")
            res = await session.call_tool("sequence_pad", arguments={
                "sequences": [[1, 2, 3], [4, 5]],
                "maxlen": 5
            })
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Padding: {res.content[0].text}")
            else:
                 print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

    print("--- DL Server Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
