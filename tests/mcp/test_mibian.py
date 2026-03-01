
import pytest
from mcp.client.stdio import stdio_client

from tests.mcp.client_utils import SafeClientSession as ClientSession
from tests.mcp.client_utils import get_server_params


@pytest.mark.asyncio
async def test_mibian_real_simulation():
    """
    REAL SIMULATION: Verify Mibian Server (Options Pricing).
    """
    params = get_server_params("mibian_server", extra_dependencies=["mibian"])

    # BS Parameters
    S = 100  # Underlying Price
    K = 100  # Strike
    r = 5    # Risk-free rate (5%)
    t = 30   # Days to exp
    v = 20   # Volatility (20%)

    print("\n--- Starting Real-World Simulation: Mibian Server ---")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. BS Price
            # 1. BS Price
            print(f"1. BS Price (S={S}, K={K}, t={t}, v={v})...")

            # Correct arguments matching server.py definition
            args = {"underlying": S, "strike": K, "interest": r, "days": t, "volatility": v}

            res = await session.call_tool("calculate_bs_price", arguments=args)
            if not res.isError:
                print(f" \033[92m[PASS]\033[0m Price: {res.content[0].text}")
            else:
                 print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

            # 2. Greeks (Delta)
            print("2. BS Delta...")
            res = await session.call_tool("calculate_bs_delta", arguments=args)
            if not res.isError:
                print(f" \033[92m[PASS]\033[0m Delta: {res.content[0].text}")

            # 3. IV Calculation
            print("3. Implied Volatility (Price=3.5)...")
            iv_args = {"underlying": S, "strike": K, "interest": r, "days": t, "call_price": 3.5}
            res = await session.call_tool("calculate_implied_volatility", arguments=iv_args)
            if not res.isError:
                print(f" \033[92m[PASS]\033[0m IV: {res.content[0].text}%")

            # 4. Bulk Option Chain
            print("4. Option Chain (S=100, K=[90,100,110])...")
            # bulk tool 'price_option_chain' expects a list of dicts in 'data' argument
            # Check server.py: async def price_option_chain(data: list[dict]) -> str:

            chain_data = [
                {"underlying": S, "strike": k, "interest": r, "days": t, "volatility": v}
                for k in [90, 100, 110]
            ]

            res = await session.call_tool("price_option_chain", arguments={"data": chain_data})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Chain: {res.content[0].text[:1000]}...")

    print("--- Mibian Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
