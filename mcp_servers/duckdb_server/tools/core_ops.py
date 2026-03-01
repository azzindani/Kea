import duckdb
import os
import structlog
from typing import Dict, Any, Optional

logger = structlog.get_logger()

# Global connection state
# DuckDB can operate on a file or in-memory (:memory:)
# We will use a singleton connection pattern.
CONN = None
DB_PATH = "project_data.duckdb" # Default persistent DB

def connect_db(path: str = "project_data.duckdb") -> str:
    """Connect to a specific DB file (or :memory:)."""
    global CONN, DB_PATH
    
    if CONN:
        try:
            CONN.close()
        except:
            pass
            
    DB_PATH = path
    try:
        CONN = duckdb.connect(DB_PATH)
        return f"Connected to DuckDB at {DB_PATH}"
    except Exception as e:
        CONN = None
        return f"Error connecting to {DB_PATH}: {e}"

def get_connection():
    """Get active connection, creating default if needed."""
    global CONN
    if CONN is None:
        connect_db(DB_PATH)
    return CONN

def get_version() -> str:
    """Return DuckDB version."""
    # hacky way if pkg version not exposed in query directly easily
    import importlib.metadata
    try:
        return importlib.metadata.version("duckdb")
    except:
        return "unknown"

def list_extensions() -> str:
    """Show installed extensions."""
    con = get_connection()
    try:
        # v0.10+ uses duckdb_extensions()
        df = con.execute("SELECT * FROM duckdb_extensions()").df()
        return df.to_markdown(index=False)
    except Exception as e:
        return f"Error listing extensions: {e}"

def install_extension(name: str) -> str:
    """Install httpfs, spatial, etc."""
    con = get_connection()
    try:
        con.execute(f"INSTALL {name}; LOAD {name};")
        return f"Extension {name} installed and loaded."
    except Exception as e:
        return f"Error installing {name}: {e}"

def load_extension(name: str) -> str:
    """Load separate extension."""
    con = get_connection()
    try:
        con.execute(f"LOAD {name};")
        return f"Extension {name} loaded."
    except Exception as e:
        return f"Error loading {name}: {e}"

def get_current_db_path() -> str:
    """Return current connection path."""
    return DB_PATH

def close_connection() -> str:
    """Explicitly close."""
    global CONN
    if CONN:
        CONN.close()
        CONN = None
        return "Connection closed."
    return "No active connection."

def set_config(key: str, value: str) -> str:
    """Set PRAGMA (threads, memory_limit)."""
    con = get_connection()
    try:
        # SAFE PRAGMA EXECUTION
        # Basic injection check
        if any(c in key for c in [";", "--", " "]):
             return "Invalid config key (potential injection)"
        
        con.execute(f"PRAGMA {key}='{value}';")
        return f"Config {key} set to {value}"
    except Exception as e:
        return f"Error setting config: {e}"
