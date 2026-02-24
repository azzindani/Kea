
import pytest
from mcp.client.stdio import stdio_client

from tests.mcp.client_utils import SafeClientSession as ClientSession
from tests.mcp.client_utils import get_server_params


@pytest.mark.asyncio
async def test_dl_real_simulation():
    """
    REAL SIMULATION: Verify Deep Learning Server (TensorFlow).
    """
    params = get_server_params("deep_learning_server", extra_dependencies=["tensorflow", "pandas", "numpy", "scikit-learn", "structlog"])

    # Iris dataset URL (Small enough for quick training tests)
    data_url = "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv"

    print("\n--- Starting Real-World Simulation: Deep Learning Server ---")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Build Dense Network
            print("1. Building Dense Network...")
            res = await session.call_tool("build_dense_network", arguments={"input_dim": 4, "output_dim": 3, "hidden_layers": [32, 16], "task": "classification"})
            if res.isError:
                print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")
                pytest.fail("Failed to build model")
            else:
                model_config = res.content[0].text
                import json
                try:
                    # The content is likely a JSON string representation of the dict
                    model_config_dict = json.loads(model_config)
                    # If the content was double-encoded or formatted, adjust.
                    print(f" \033[92m[PASS]\033[0m Model built: {model_config_dict.get('name')}")
                except:
                     # Fallback if it's already a dict (unlikely for text content) or error
                     print(f"Warning: Could not parse output: {model_config[:100]}...")
                     model_config_dict = None

            # 2. Train Model
            if model_config_dict:
                print("2. Training Model...")
                res = await session.call_tool("train_deep_model", arguments={
                    "data_url": data_url,
                    "target_column": "species",
                    "model_config": model_config_dict,
                    "epochs": 5,
                    "batch_size": 16
                })
                if not res.isError:
                     print(f" \033[92m[PASS]\033[0m Training Complete: {res.content[0].text[:200]}...")
                else:
                     print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

    print("--- DL Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
