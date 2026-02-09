
import sys
import os
from pathlib import Path

# Add root to sys.path
root_path = os.getcwd()
if root_path not in sys.path:
    sys.path.append(root_path)

print(f"Checking imports for newspaper_server...")
try:
    # Try importing the tools module which triggered the error
    from mcp_servers.newspaper_server.tools import core
    print("Successfully imported tools.core")
except ImportError as e:
    print(f"Failed to import tools.core: {e}")
    sys.exit(1)

try:
    # Try importing the server module
    from mcp_servers.newspaper_server import server
    print("Successfully imported server module")
except ImportError as e:
    print(f"Failed to import server module: {e}")
    sys.exit(1)

print("All imports successful.")
