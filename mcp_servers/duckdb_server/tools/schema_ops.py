from mcp_servers.duckdb_server.tools import core_ops
from typing import Dict, Any, Optional

def create_table(table_name: str, columns: Dict[str, str]) -> str:
    """Basic Create Table (columns dict: name -> type)."""
    con = core_ops.get_connection()
    cols_def = ", ".join([f"{k} {v}" for k,v in columns.items()])
    query = f"CREATE TABLE {table_name} ({cols_def})"
    try:
        con.execute(query)
        return f"Table {table_name} created."
    except Exception as e:
        return f"Error: {e}"

def drop_table(table_name: str) -> str:
    """Drop table if exists."""
    con = core_ops.get_connection()
    try:
        con.execute(f"DROP TABLE IF EXISTS {table_name}")
        return f"Table {table_name} dropped."
    except Exception as e:
        return f"Error: {e}"

def alter_table_rename(old_name: str, new_name: str) -> str:
    """Rename table."""
    con = core_ops.get_connection()
    try:
        con.execute(f"ALTER TABLE {old_name} RENAME TO {new_name}")
        return f"Renamed {old_name} to {new_name}."
    except Exception as e:
        return f"Error: {e}"

def add_column(table_name: str, column_name: str, column_type: str) -> str:
    """Alter table add column."""
    con = core_ops.get_connection()
    try:
        con.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
        return f"Column {column_name} added to {table_name}."
    except Exception as e:
        return f"Error: {e}"

def create_index(index_name: str, table_name: str, column_name: str) -> str:
    """Create index on column."""
    con = core_ops.get_connection()
    try:
        con.execute(f"CREATE INDEX {index_name} ON {table_name} ({column_name})")
        return f"Index {index_name} created."
    except Exception as e:
        return f"Error: {e}"

def drop_index(index_name: str) -> str:
    """Drop index."""
    con = core_ops.get_connection()
    try:
        con.execute(f"DROP INDEX IF EXISTS {index_name}")
        return f"Index {index_name} dropped."
    except Exception as e:
        return f"Error: {e}"

def create_view(view_name: str, query: str) -> str:
    """Create view from query."""
    con = core_ops.get_connection()
    try:
        con.execute(f"CREATE OR REPLACE VIEW {view_name} AS {query}")
        return f"View {view_name} created."
    except Exception as e:
        return f"Error: {e}"

def drop_view(view_name: str) -> str:
    """Drop view."""
    con = core_ops.get_connection()
    try:
        con.execute(f"DROP VIEW IF EXISTS {view_name}")
        return f"View {view_name} dropped."
    except Exception as e:
        return f"Error: {e}"

def truncate_table(table_name: str) -> str:
    """Delete all rows."""
    con = core_ops.get_connection()
    try:
        con.execute(f"DELETE FROM {table_name}")
        return f"Table {table_name} truncated."
    except Exception as e:
        return f"Error: {e}"
