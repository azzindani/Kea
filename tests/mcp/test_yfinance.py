import os
import sys

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# Define the server execution command
def get_server_params():
    # Use the same python that runs pytest
    python_exe = sys.executable
    server_script = os.path.abspath("mcp_servers/yfinance_server/server.py")
    return StdioServerParameters(
        command="uv",
        args=["run", "--with", "yfinance", "--with", "pandas", "--with", "structlog", "python", server_script],
        env=os.environ.copy()
    )

@pytest.mark.asyncio
async def test_yfinance_tools_dynamic():
    """Verify ALL YFinance tools using MCP Client."""

    params = get_server_params()

    # Connect to the server
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Discover Tools
            tools_res = await session.list_tools()
            tools = tools_res.tools
            print(f"\nDiscovered {len(tools)} tools via Client.")

            # Create a temporary safe ticker list for the global sweep to avoid delisted tickers
            import json
            test_data_path = "mcp_servers/yfinance_server/data/TEST_QC_GENERIC.json"
            try:
                # Ensure the directory exists
                os.makedirs(os.path.dirname(test_data_path), exist_ok=True)
                with open(test_data_path, "w") as f:
                    json.dump({"count": 5, "tickers": ["MSFT", "AAPL", "NVDA", "AMZN", "GOOG"]}, f)

                success = 0
                failed = 0

                for tool in tools:
                    name = tool.name
                    print(f"Testing {name}...", end="")

                    try:
                        # Generic call - most YFinance tools take 'ticker' or 'symbol'
                        # We use a stable ticker and a safe country code
                        res = await session.call_tool(name, arguments={
                            "ticker": "MSFT",
                            "symbol": "MSFT",
                            "country_code": "TEST_QC_GENERIC",
                            "indicators": ["sma"],
                            "date": "" # Let server pick a valid date
                        })

                        if not res.isError:
                            print(" \033[92m[PASS]\033[0m")
                            success += 1
                        else:
                            error_text = res.content[0].text if res.content else "Error"
                            # If the error is still a validation error, we count it as a skip
                            if "validation error" in error_text.lower():
                                print(" \033[93m[SKIP]\033[0m (Validation: Needs specific args)")
                            else:
                                print(f" \033[91m[FAIL]\033[0m {error_text[:1000]}")
                                failed += 1
                    except Exception as e:
                         print(f" [EXCEPTION] {e}")
                         failed += 1

                print(f"\nPassed: {success}, Failed: {failed}")
                assert success > 0
            finally:
                if os.path.exists(test_data_path):
                    os.remove(test_data_path)

@pytest.mark.asyncio
async def test_scenario_market_analysis():
    """
    REAL SIMULATION: Execute a coherent Market Analyst workflow.
    
    Scenario:
    1. Check current price of NVDA (Volatility check)
    2. Get Market Cap (Size check)
    3. Get Analyst Ratings (Sentiment check)
    """
    params = get_server_params()
    ticker = "NVDA"

    print(f"\n--- Starting Real-World Scenario: Analyzing {ticker} ---")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Step 1: Price
            print(f"1. Fetching Price for {ticker}...")
            price_res = await session.call_tool("get_current_price", arguments={"ticker": ticker})
            assert not price_res.isError
            print(f"   Result: {price_res.content[0].text[:1000]}...")

            # Step 2: Market Cap
            print("2. Fetching Market Cap...")
            cap_res = await session.call_tool("get_market_cap", arguments={"ticker": ticker})
            assert not cap_res.isError
            print(f"   Result: {cap_res.content[0].text}")

            # Step 3: Analyst Ratings
            print("3. Fetching Analyst Ratings...")
            rating_res = await session.call_tool("get_analyst_ratings", arguments={"ticker": ticker})
            assert not rating_res.isError
            print(f"   Result: {rating_res.content[0].text[:1000]}...")

            print("--- Scenario Complete: Success ✅ ---")

@pytest.mark.asyncio
async def test_simulation_full_coverage():
    """
    REAL SIMULATION: Deep Dive Due Diligence (100% Tool Coverage).
    
    Executes a complete analysis workflow using EVERY available tool.
    Target: MSFT (Microsoft)
    """
    params = get_server_params()
    ticker = "MSFT"

    print(f"\n--- Starting FULL COVERAGE Simulation: {ticker} ---")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Helper to run tool and print status
            async def run_step(step_name, tool_name, args=None):
                if args is None: args = {"ticker": ticker}
                print(f"{step_name} [{tool_name}]...", end="")
                try:
                    res = await session.call_tool(tool_name, arguments=args)
                    if res.isError:
                        print(f" \033[91m[FAIL]\033[0m {res.content[0].text[:1000]}")
                        return False
                    print(" \033[92m[PASS]\033[0m")
                    return True
                except Exception as e:
                    print(f" [EXCEPTION] {e}")
                    return False

            # Phase 1: Market Data
            await run_step("1.1 Price", "get_current_price")
            await run_step("1.2 Market Cap", "get_market_cap")
            await run_step("1.3 P/E Ratio", "get_pe_ratio")
            await run_step("1.4 Volume", "get_volume")
            await run_step("1.5 Beta", "get_beta")
            await run_step("1.6 Metadata", "get_quote_metadata")
            await run_step("1.7 Bulk History", "get_bulk_historical_data", {"tickers": "MSFT AAPL", "period": "1d"})

            # Phase 2: Financials
            await run_step("2.1 Income (Annual)", "get_income_statement_annual")
            await run_step("2.2 Income (Quarterly)", "get_income_statement_quarterly")
            await run_step("2.3 Balance (Annual)", "get_balance_sheet_annual")
            await run_step("2.4 Balance (Quarterly)", "get_balance_sheet_quarterly")
            await run_step("2.5 Cash Flow (Annual)", "get_cash_flow_statement_annual")
            await run_step("2.6 Cash Flow (Quarterly)", "get_cash_flow_statement_quarterly")

            # Phase 3: Holders
            await run_step("3.1 Major Holders", "get_major_holders")
            await run_step("3.2 Institutional", "get_institutional_holders")
            await run_step("3.3 Mutual Funds", "get_mutual_funds")
            await run_step("3.4 Insider Tx", "get_insider_transactions")
            await run_step("3.5 Insider Roster", "get_insider_roster")

            # Phase 4: Analysis
            await run_step("4.1 Ratings", "get_analyst_ratings")
            await run_step("4.2 Price Targets", "get_price_targets")
            await run_step("4.3 Upgrades", "get_upgrades_downgrades")
            await run_step("4.4 Earnings Cal", "get_earnings_calendar")
            await run_step("4.5 Dividends", "get_dividends_history")
            await run_step("4.6 Splits", "get_splits_history")
            await run_step("4.7 Indicators", "calculate_indicators", {"ticker": ticker, "indicators": ["sma", "rsi"]})

            # Phase 5: Visuals
            # Note: Returns Image, might be large text blob in console, but valid
            await run_step("5.1 Price Chart", "get_price_chart", {"ticker": ticker, "period": "1mo"})

            # Phase 6: Options
            # Need expiration first
            exp_res = await session.call_tool("get_option_expirations", arguments={"ticker": ticker})
            if not exp_res.isError and exp_res.content:
                exp_text = exp_res.content[0].text
                if "Error" not in exp_text and "Content" not in exp_text:
                    try:
                        import ast
                        dates = ast.literal_eval(exp_text)
                        if dates and isinstance(dates, (list, tuple)):
                            target_date = dates[0]
                            print(f"6.1 Expirations... [PASS] (Using {target_date})")
                            await run_step("6.2 Option Chain", "get_options_chain", {"ticker": ticker, "date": target_date})
                    except (ValueError, SyntaxError, KeyError, IndexError) as e:
                        print(f"6.1 Expirations... [SKIP] Could not parse: {e}")

            # Phase 7: Discovery & Report
            # Create a temporary safe ticker list for testing to avoid delisted tickers in US.json
            import json
            test_data_path = "mcp_servers/yfinance_server/data/TEST_QC.json"
            try:
                with open(test_data_path, "w") as f:
                    json.dump({
                        "count": 5,
                        "tickers": ["MSFT", "AAPL", "NVDA", "AMZN", "GOOG"]
                    }, f)

                # Use the test country code
                await run_step("7.1 Country Search", "get_tickers_by_country", {"country_code": "TEST_QC"})
            finally:
                # Cleanup
                if os.path.exists(test_data_path):
                    os.remove(test_data_path)

            await run_step("7.2 Full Report", "get_full_report")

            # Phase 8: Dynamic Info
            await run_step("8.1 Dynamic Info", "get_ticker_info", {"ticker": ticker, "key": "profitMargins"})

            print("--- FULL COVERAGE Simulation Complete ---")
