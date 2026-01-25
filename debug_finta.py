
from finta import TA
import inspect

def list_finta_tools():
    methods = [m for m in dir(TA) if not m.startswith("__") and callable(getattr(TA, m))]
    print(f"Total Finta Tools: {len(methods)}")
    print(methods)

if __name__ == "__main__":
    list_finta_tools()
