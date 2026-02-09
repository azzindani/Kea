
try:
    import newspaper
    print("Successfully imported 'newspaper'")
    print(f"Newspaper version: {newspaper.__version__}")
except ImportError as e:
    print(f"Failed to import 'newspaper': {e}")

try:
    import newspaper4k
    print("Successfully imported 'newspaper4k'")
except ImportError as e:
    print(f"Failed to import 'newspaper4k': {e}")
