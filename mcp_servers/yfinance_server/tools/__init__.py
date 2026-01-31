# Yfinance Server Tools
"""Auto-discovered with actual export detection."""

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
