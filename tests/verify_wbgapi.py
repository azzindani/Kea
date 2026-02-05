
import asyncio
from mcp_servers.wbgapi_server.server import WbgapiServer

async def verify():
    print("--- Verifying World Bank (wbgapi) Server ---")
    server = WbgapiServer()
    tools = server.get_tools()
    print(f"Total Tools Registered: {len(tools)}")
    
    # Test 1: Unrolled Indicator (GDP for USA/CHN)
    print("\n--- Testing Indicator: GDP (USA, CHN) ---")
    try:
        handler = server._handlers["get_gdp"]
        # Default MRV=5
        res = await handler({"economies": ["USA", "CHN"]})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:300])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Exception: {e}")

    # Test 2: Dashboard (Climate)
    print("\n--- Testing Dashboard: Climate (USA) ---")
    try:
        handler = server._handlers["get_climate_dashboard"]
        # Default MRV=1
        res = await handler({"economies": ["USA"]})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:300])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
         print(f"Exception: {e}")

    # Test 3: Search (Poverty)
    print("\n--- Testing Search: Indicators (Poverty) ---")
    try:
        handler = server._handlers["search_indicators"]
        res = await handler({"query": "poverty"})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:300])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
         print(f"Exception: {e}")

    # Test 4: Phase 2 Education Stats
    print("\n--- Testing Education Stats (DB=12) ---")
    try:
        handler = server._handlers["get_education_stats"]
        res = await handler({"economies": ["USA"]})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:300])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
         print(f"Exception: {e}")
         
    # Test 5: Phase 2 Income Level Data
    print("\n--- Testing Income Group Aggregates (GDP) ---")
    try:
        handler = server._handlers["get_income_level_data"]
        # GDP code: NY.GDP.MKTP.CD
        res = await handler({"indicator_code": "NY.GDP.MKTP.CD"})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:300])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
         print(f"Exception: {e}")

    except Exception as e:
         print(f"Exception: {e}")
         
    # Test 6: Phase 3 Food Security Dashboard
    print("\n--- Testing Food Security Dashboard (USA) ---")
    try:
        handler = server._handlers["get_food_security_dashboard"]
        # Default MRV=1
        res = await handler({"economies": ["USA"]})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:300])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
         print(f"Exception: {e}")

    except Exception as e:
         print(f"Exception: {e}")
         
    # Test 7: Phase 4 Debt (IDS)
    print("\n--- Testing International Debt (IDS) ---")
    try:
        handler = server._handlers["get_debt_stats"]
        # Default MRV=5
        # Use a developing country usually in IDS (e.g. BRA, IND, MEX)
        res = await handler({"economies": ["BRA"]})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:300])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
         print(f"Exception: {e}")
         
    # Test 8: Phase 4 Governance (WGI)
    print("\n--- Testing Governance (WGI) ---")
    try:
        handler = server._handlers["get_governance_data"]
        res = await handler({"economies": ["USA", "FIN"]})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:300])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
         print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
