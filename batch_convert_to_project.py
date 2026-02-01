
import os
import re
from pathlib import Path

# List of failing servers based on logs
TARGET_SERVERS = [
    "matplotlib_server",
    "bs4_server",
    "pandas_server", 
    "seaborn_server",
    "quantstats_server", 
    "sec_edgar_server",
    "portfolio_server",
    "docx_server",
    "wbgapi_server",
    "newspaper_server",
    "tradingview_server",
    "web3_server",
    "pdr_server",
    "ccxt_server",
    "scraper_server"
]

ROOT_DIR = Path("mcp_servers")

TEMPLATE_TOML = """[project]
name = "{server_name}"
version = "0.1.0"
description = "MCP Server for {server_name}"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
{dependencies}
]

[tool.uv]
dev-dependencies = []
"""

def extract_dependencies(content):
    # Regex to find dependencies list in the /// script block
    match = re.search(r'# dependencies = \[\s*(.*?)\s*# \]', content, re.DOTALL)
    if not match:
        return ["mcp", "structlog"] # Default fallback
    
    raw_deps = match.group(1)
    # Clean up quotes and commas
    deps = [d.strip().replace('"', '').replace(',', '') for d in raw_deps.splitlines() if d.strip()]
    return deps

def convert_server(server_name):
    server_dir = ROOT_DIR / server_name
    server_file = server_dir / "server.py"
    toml_file = server_dir / "pyproject.toml"

    if not server_file.exists():
        print(f"⚠️ {server_name}: server.py not found.")
        return

    try:
        with open(server_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 1. Extract Deps
        deps = extract_dependencies(content)
        # Ensure critical ones are there
        if "mcp" not in deps: deps.append("mcp")
        # Format for TOML
        deps_str = "    " + ",\n    ".join([f'"{d}"' for d in deps])

        # 2. Write pyproject.toml
        toml_content = TEMPLATE_TOML.format(server_name=server_name, dependencies=deps_str)
        with open(toml_file, "w", encoding="utf-8") as f:
            f.write(toml_content)
        
        # 3. Strip Inline Metadata from server.py & Apply Matplotlib Fix
        lines = content.splitlines()
        new_lines = []
        in_metadata = False
        
        # Check if we need matplotlib fix
        has_matplotlib = "matplotlib" in deps or "seaborn" in deps or "quantstats" in deps
        matplotlib_fixed = False
        
        for line in lines:
            if line.strip() == "# /// script":
                in_metadata = True
                continue
            if in_metadata and line.strip() == "# ///":
                in_metadata = False
                continue
            if in_metadata:
                continue
                
            # Inject matplotlibAgg fix if needed and not present
            if has_matplotlib and not matplotlib_fixed and ("import matplotlib" in line or "from mcp.server.fastmcp" in line):
                 if "matplotlib.use" not in content:
                     new_lines.append("import matplotlib")
                     new_lines.append('matplotlib.use("Agg")')
                     matplotlib_fixed = True # Only add once
            
            new_lines.append(line)

        with open(server_file, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines))

        print(f"✅ Converted {server_name}: Created pyproject.toml with {len(deps)} deps + Cleaned server.py")

    except Exception as e:
        print(f"❌ Failed to convert {server_name}: {e}")

def main():
    print("🚀 Batch Converting Failing Servers to Project Mode...")
    for server in TARGET_SERVERS:
        convert_server(server)

if __name__ == "__main__":
    main()
