import sys
import os

sys.path.append(os.getcwd())

servers_to_check = ["finta_server", "academic_server", "yfinance_server"]
print(f"Checking imports for: {servers_to_check}")

for s in servers_to_check:
    try:
        module = __import__(f"mcp_servers.{s}", fromlist=["*"])
        print(f"✅ Imported {s}")
        print(f"   Exports: {dir(module)[:5]}...") # Show first few exports
    except ImportError as e:
        print(f"❌ Failed to import {s}: {e}")
    except Exception as e:
        print(f"❌ Error importing {s}: {e}")
