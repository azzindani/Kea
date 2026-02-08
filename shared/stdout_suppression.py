
import sys
import os
from contextlib import contextmanager
from io import StringIO
import logging

@contextmanager
def suppress_stdout():
    """
    Context manager to redirect stdout to devnull to prevent
    library logs from breaking MCP JSON-RPC protocol.
    """
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout

@contextmanager
def redirect_stdout_to_stderr():
    """
    Context manager to redirect stdout to stderr.
    Useful when you want to see the output but not on stdout.
    """
    old_stdout = sys.stdout
    sys.stdout = sys.stderr
    try:
        yield
    finally:
        sys.stdout = old_stdout
