
import hashlib
import sys
from pathlib import Path

def get_hash(path):
    try:
        content = Path(path).read_bytes()
        return hashlib.md5(content).hexdigest()
    except Exception as e:
        return f"ERROR: {e}"

def check_string_in_file(path, search_str):
    try:
        content = Path(path).read_text(encoding="utf-8")
        return search_str in content
    except:
        return False

print("=== INTEGRITY CHECK ===")
files = {
    "services/mcp_host/core/session_registry.py": "Has '--no-project'",
    "mcp_servers/yfinance_server/server.py": "Has PEP 723 Header",
}

for f, desc in files.items():
    p = Path(f)
    print(f"\nChecking {f}...")
    if not p.exists():
        print("  ❌ FILE MISSING")
        continue
        
    h = get_hash(p)
    print(f"  MD5: {h}")
    
    if "session_registry.py" in f:
        has_flag = check_string_in_file(f, "--no-project")
        print(f"  Contains '--no-project': {'✅ YES' if has_flag else '❌ NO'}")
        has_with = check_string_in_file(f, "--with mcp")
        print(f"  Contains '--with mcp':   {'✅ YES' if has_with else '❌ NO'}")

    if "server.py" in f:
        has_header = check_string_in_file(f, "# /// script")
        print(f"  Contains PEP 723 Header: {'✅ YES' if has_header else '❌ NO'}")

print("\n=== ENVIRONMENT ===")
try:
    import mcp
    print(f"mcp version: {mcp.__file__}")
except ImportError:
    print("❌ mcp package NOT installed in this python environment")
    
import sys
print(f"Python: {sys.executable}")
