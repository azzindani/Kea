
import sys
import os
from pathlib import Path

# Add project root to path
root_path = Path(__file__).resolve().parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

import asyncio
from services.mcp_host.core.session_registry import SessionRegistry
from shared.logging import get_logger



import logging
import sys

# Configure logging to stdout
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
logger = logging.getLogger("services.mcp_host.core.session_registry")
logger.addHandler(handler)
logger.setLevel(logging.INFO)

async def main():
    print("--- Starting Discovery Debug ---")
    # Force re-discovery if needed, but new instance does it.
    registry = SessionRegistry()
    
    print(f"\nDiscovered Servers: {list(registry.server_configs.keys())}")
    
    python_server_config = registry.server_configs.get("python_server")
    if python_server_config:
        print(f"python_server found at: {python_server_config.script_path}")
    else:
        print("python_server NOT found")

    # print(f"\nTool to Server Mapping: {registry.tool_to_server}")
    
    if "execute_code" in registry.tool_to_server:
        print(f"execute_code found in: {registry.tool_to_server['execute_code']}")
    else:
        print("execute_code tool NOT found in registry")
        
    print("--- End Discovery Debug ---")

if __name__ == "__main__":
    asyncio.run(main())
