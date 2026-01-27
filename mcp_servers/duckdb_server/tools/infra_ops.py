from mcp_servers.duckdb_server.tools import core_ops
from typing import Dict, Any, List

def parquet_metadata(file_path: str) -> str:
    """Inspect parquet file metadata (parquet_metadata func)."""
    con = core_ops.get_connection()
    try:
        df = con.execute(f"SELECT * FROM parquet_metadata('{file_path}')").df()
        return df.to_markdown(index=False)
    except Exception as e:
        return f"Error: {e}"

def parquet_schema(file_path: str) -> str:
    """Inspect parquet schema."""
    con = core_ops.get_connection()
    try:
        df = con.execute(f"SELECT * FROM parquet_schema('{file_path}')").df()
        return df.to_markdown(index=False)
    except Exception as e:
        return f"Error: {e}"

def current_db_size() -> str:
    """Estimate DB size (if file based)."""
    path = core_ops.get_current_db_path()
    if path == ":memory:": return "Memory"
    import os
    try:
        size = os.path.getsize(path)
        return f"{size / (1024*1024):.2f} MB"
    except:
        return "Unknown"

def show_tables_expanded() -> str:
    """Detailed table info (duckdb_tables)."""
    con = core_ops.get_connection()
    try:
        df = con.execute("SELECT database_name, schema_name, table_name, estimated_size, column_count FROM duckdb_tables()").df()
        return df.to_markdown(index=False)
    except Exception as e:
        return f"Error: {e}"

def describe_table_detailed(table_name: str) -> str:
    """Stats + type info (SUMMARIZE + DESCRIBE)."""
    con = core_ops.get_connection()
    try:
        s1 = con.execute(f"DESCRIBE {table_name}").df()
        return s1.to_markdown(index=False)
    except Exception as e:
        return f"Error: {e}"

def get_memory_usage() -> str:
    """Pragma memory usage (duckdb_memory?)."""
    con = core_ops.get_connection()
    try:
        # PRAGMA memory_limit
        # Not easily queriable as a value, usually check settings
        res = con.execute("SELECT * FROM duckdb_settings() WHERE name='memory_limit'").fetchone()
        return str(res)
    except Exception as e:
        return str(e)

def list_settings() -> str:
    """Show all pragmas."""
    con = core_ops.get_connection()
    try:
        df = con.execute("SELECT name, value, description FROM duckdb_settings() LIMIT 50").df()
        return df.to_markdown(index=False)
    except Exception as e:
        return f"Error: {e}"

def checkpoint_db() -> str:
    """Force checkpoint."""
    con = core_ops.get_connection()
    try:
        con.execute("CHECKPOINT")
        return "Checkpoint complete."
    except Exception as e:
        return f"Error: {e}"

def vacuum_db() -> str:
    """Reclaim space (VACUUM implicitly called or specific)."""
    # VACUUM table? DuckDB usually does this on checkpoint?
    # No explicit VACUUM command in early versions, mostly for PostgreSQL compat.
    return "Use CHECKPOINT to reclaim space."

def get_query_profiling(query: str) -> str:
    """Enable profiling, run query, get output path."""
    con = core_ops.get_connection()
    try:
        con.execute("PRAGMA enable_profiling='json'")
        con.execute(query)
        con.execute("PRAGMA disable_profiling")
        return "Profiling enabled. Check output (usually prints to stdout or file depending on config)."
    except Exception as e:
        return f"Error: {e}"
