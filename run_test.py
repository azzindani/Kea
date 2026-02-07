import sys
import os
import asyncio

# Add current directory to path so we can import 'mcp_servers'
sys.path.append(os.getcwd())

print("Attempting import...")
try:
    from mcp_servers.finta_server.server import FintaServer
    print("Import Successful")
except Exception as e:
    print(f"Import Failed: {e}")
    sys.exit(1)

async def run():
    print("Instantiating Server...")
    server = FintaServer()
    print("Getting Tools...")
    tools = server.get_tools()
    print(f"Found {len(tools)} tools")

if __name__ == "__main__":
    asyncio.run(run())
