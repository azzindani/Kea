import os
from pathlib import Path

SERVERS_DIR = Path("mcp_servers")
TEMPLATE = """# {NAME_TITLE}
\"\"\"Auto-discovered with actual export detection.\"\"\"

from pathlib import Path
from typing import Any
import importlib

_DIR = Path(__file__).parent
_discovered: dict = {}


def _discover() -> dict:
    global _discovered
    if _discovered:
        return _discovered
    exports = {}
    for item in _DIR.iterdir():
        if item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
            module_path = f".{item.stem}"
            try:
                module = importlib.import_module(module_path, package=__name__)
                for name in dir(module):
                    if not name.startswith("_"):
                        obj = getattr(module, name, None)
                        if isinstance(obj, type) or callable(obj):
                            exports[name] = module_path
            except Exception:
                continue
    _discovered = exports
    return exports


def __getattr__(name: str) -> Any:
    exports = _discover()
    if name in exports:
        module = importlib.import_module(exports[name])
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return list(_discover().keys())


# Lazy discovery to prevent import loops
# __all__ = list(_discover())
__all__ = []
"""

def standardize_init():
    updated = 0
    created = 0
    skipped = 0
    
    if not SERVERS_DIR.exists():
        print(f"Error: {SERVERS_DIR} not found")
        return

    for item in SERVERS_DIR.iterdir():
        # Check if it is a directory and has server.py
        if item.is_dir() and (item / "server.py").exists():
            init_file = item / "__init__.py"
            
            # Format title: "academic_server" -> "Academic Server"
            name_title = item.name.replace("_", " ").title()
            
            # Use replace instead of format to avoid brace issues
            content = TEMPLATE.replace("{NAME_TITLE}", name_title)
            
            if not init_file.exists():
                print(f"Creating: {item.name}/__init__.py")
                init_file.write_text(content, encoding="utf-8")
                created += 1
            else:
                # Read existing to see if it needs update
                current = init_file.read_text(encoding="utf-8")
                if current.strip() != content.strip():
                    print(f"Updating: {item.name}/__init__.py")
                    init_file.write_text(content, encoding="utf-8")
                    updated += 1
                else:
                    skipped += 1
                    
    print(f"\nSummary:")
    print(f"Created: {created}")
    print(f"Updated: {updated}")
    print(f"Skipped: {skipped}")
    print(f"Total Reviewed: {created + updated + skipped}")

if __name__ == "__main__":
    standardize_init()
