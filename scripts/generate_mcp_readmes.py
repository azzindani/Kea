import os
import re
import glob
from pathlib import Path

MCP_SERVERS_DIR = r"d:\Antigravity\Kea\mcp_servers"

def extract_tools(server_path):
    server_file = os.path.join(server_path, "server.py")
    if not os.path.exists(server_file):
        return None, []
    
    with open(server_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extract server name
    name_match = re.search(r'FastMCP\("([^"]+)"', content)
    server_name = name_match.group(1) if name_match else os.path.basename(server_path)
    
    # Extract dependencies
    deps_match = re.search(r'dependencies=\[([^\]]+)\]', content)
    deps = []
    if deps_match:
        raw_deps = deps_match.group(1)
        deps = [d.strip().strip('"').strip("'") for d in raw_deps.split(",") if d.strip()]
        
    # Extract tools
    tools = []
    # simple regex to find async def or def after @mcp.tool()
    matches = re.finditer(r'@mcp\.tool\(\)\s+(?:async\s+)?def\s+([a-zA-Z0-9_]+)\((.*?)\)(?:\s*->\s*.*?)?:', content, re.DOTALL)
    
    for m in matches:
        tool_name = m.group(1)
        sig = m.group(2)
        tools.append({"name": tool_name, "signature": sig})
        
    return server_name, deps, tools

def generate_readme(server_path, force=False):
    readme_path = os.path.join(server_path, "README.md")
    
    if os.path.exists(readme_path) and not force:
        size = os.path.getsize(readme_path)
        if size > 300: # heuristic for "already good"
            print(f"Skipping {os.path.basename(server_path)} (README exists and > 300 bytes)")
            return
            
    server_name, deps, tools = extract_tools(server_path)
    if not tools and not deps:
        print(f"Skipping {os.path.basename(server_path)} (No tools found)")
        return

    print(f"Generating README for {server_name}...")
    
    clean_name = server_name.replace("_", " ").title()
    
    md = f"# 🔌 {clean_name}\n\n"
    md += f"The `{server_name}` is an MCP server providing tools for **{clean_name}** functionality.\n"
    md += "It is designed to be used within the Kea ecosystem.\n\n"
    
    md += "## 🧰 Tools\n\n"
    if tools:
        md += "| Tool | Description | Arguments |\n"
        md += "|:-----|:------------|:----------|\n"
        for tool in tools:
            # We don't have descriptions, so we'll leave that column generic or empty
            # args can be cleaned up
            args = tool['signature'].replace("\n", " ")
            md += f"| `{tool['name']}` | Execute {tool['name'].replace('_', ' ')} operation | `{args}` |\n"
    else:
        md += "No tools explicitly detected in `server.py`.\n"
        
    md += "\n## 📦 Dependencies\n\n"
    if deps:
        md += "The following packages are required:\n"
        for d in deps:
            md += f"- `{d}`\n"
    else:
        md += "Standard library only.\n"
        
    md += "\n## 🚀 Usage\n\n"
    md += "This server is automatically discovered by the **MCP Host**. To run it manually:\n\n"
    md += "```bash\n"
    md += f"uv run python -m mcp_servers.{os.path.basename(server_path)}.server\n"
    md += "```\n"

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(md)

def main():
    if not os.path.exists(MCP_SERVERS_DIR):
        print(f"Directory not found: {MCP_SERVERS_DIR}")
        return

    subdirs = [f.path for f in os.scandir(MCP_SERVERS_DIR) if f.is_dir()]
    
    for subdir in subdirs:
        # Ignore pycache, venv
        if os.path.basename(subdir).startswith(".") or os.path.basename(subdir).startswith("__"):
            continue
            
        generate_readme(subdir)

if __name__ == "__main__":
    main()
