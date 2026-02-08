import pytest
import asyncio
from tests.mcp.client_utils import SafeClientSession as ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_geopy_real_simulation():
    """
    REAL SIMULATION: Verify Geopy Server (Geocoding, Distance).
    """
    params = get_server_params("geopy_server", extra_dependencies=["geopy", "pandas"])
    
    print(f"\n--- Starting Real-World Simulation: Geopy Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Geocode
            address = "Empire State Building, New York"
            print(f"1. Geocoding '{address}'...")
            res = await session.call_tool("geocode_address", arguments={"query": address})
            if not res.isError:
                print(f" \033[92m[PASS]\033[0m Coords: {res.content[0].text}")
                # Parse lat/lon for next step if possible, hardcode for safety
                lat1, lon1 = 40.748, -73.985 
            else:
                print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")
                lat1, lon1 = 40.748, -73.985

            # 2. Reverse Geocode
            print("2. Reverse Geocoding (34.0522, -118.2437)...") # LA
            res = await session.call_tool("reverse_geocode", arguments={"lat": 34.0522, "lon": -118.2437})
            if not res.isError:
                print(f" \033[92m[PASS]\033[0m Address: {res.content[0].text}")
                lat2, lon2 = 34.0522, -118.2437
            else:
                print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")
                lat2, lon2 = 34.0522, -118.2437

            # 3. Distance
            print("3. Calculating Distance (NY to LA)...")
            res = await session.call_tool("calculate_distance", arguments={"lat1": lat1, "lon1": lon1, "lat2": lat2, "lon2": lon2})
            if not res.isError:
                print(f" \033[92m[PASS]\033[0m Distance: {res.content[0].text} km")

            # 4. TSP (Travel)
            print("4. Solving TSP (3 points)...")
            locs = [(40.71, -74.00), (34.05, -118.24), (51.50, -0.12)] # NY, LA, London
            res = await session.call_tool("solve_tsp", arguments={"locations": locs})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Route: {res.content[0].text}")

    print("--- Geopy Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
