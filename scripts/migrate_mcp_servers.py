
import os
from pathlib import Path

# Configuration
BASE_DIR = Path("d:/Antigravity/Kea/mcp_servers")
SHARED_IMPORT = "from shared.mcp.fastmcp import FastMCP"
OLD_IMPORT = "from mcp.server.fastmcp import FastMCP"

def migrate_server(server_path: Path):
    content = server_path.read_text(encoding="utf-8")
    
    # 1. Check if already migrated
    if SHARED_IMPORT in content:
        print(f"SKIPPED (Alive): {server_path.parent.name}")
        return

    # 2. Check if it uses FastMCP
    if "FastMCP" not in content:
        print(f"SKIPPED (Unknown): {server_path.parent.name}")
        return

    original_content = content
    
    # 3. Replace Import
    if OLD_IMPORT in content:
        content = content.replace(OLD_IMPORT, SHARED_IMPORT)
    else:
        # Pass for now
        pass

    if content != original_content:
        server_path.write_text(content, encoding="utf-8")
        print(f"MIGRATED: {server_path.parent.name}")
    else:
        print(f"SKIPPED (No changes made): {server_path.parent.name}")

def main():
    if not BASE_DIR.exists():
        print(f"Error: {BASE_DIR} does not exist")
        return

    print("Starting Bulk Migration to Shared FastMCP...")
    count = 0
    for server_dir in BASE_DIR.iterdir():
        if not server_dir.is_dir(): continue
        
        server_file = server_dir / "server.py"
        if server_file.exists():
            migrate_server(server_file)
            count += 1
            
    print(f"Processed {count} servers.")

if __name__ == "__main__":
    main()
