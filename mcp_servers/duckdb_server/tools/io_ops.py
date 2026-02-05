from mcp_servers.duckdb_server.tools import core_ops
import os

def import_csv(file_path: str, table_name: str, auto_detect: bool = True) -> str:
    """Create table from CSV (auto-detect)."""
    con = core_ops.get_connection()
    try:
        # Create table ... as select * from read_csv...
        # Option: header=True usually default in auto_detect
        query = f"CREATE TABLE {table_name} AS SELECT * FROM read_csv('{file_path}', auto_detect={str(auto_detect).lower()})"
        con.execute(query)
        return f"Table {table_name} imported from {file_path}."
    except Exception as e:
        return f"Error: {e}"

def import_parquet(file_path: str, table_name: str) -> str:
    """Create table from Parquet."""
    con = core_ops.get_connection()
    try:
        query = f"CREATE TABLE {table_name} AS SELECT * FROM read_parquet('{file_path}')"
        con.execute(query)
        return f"Table {table_name} imported from {file_path}."
    except Exception as e:
        return f"Error: {e}"

def import_json(file_path: str, table_name: str, format: str = "auto") -> str:
    """Create table from JSON. Format: auto, newline_delimited, array."""
    con = core_ops.get_connection()
    try:
        query = f"CREATE TABLE {table_name} AS SELECT * FROM read_json('{file_path}', auto_detect=true)"
        con.execute(query)
        return f"Table {table_name} imported from {file_path}."
    except Exception as e:
        return f"Error: {e}"

def export_csv(table_or_query: str, file_path: str) -> str:
    """Save table/query to CSV."""
    con = core_ops.get_connection()
    # Check if table or query. Simpler: COPY (query) TO ...
    # Syntax: COPY {table_name} TO '{file_path}' (HEADER, DELIMITER ',')
    # Or COPY (SELECT ...) TO ...
    
    # Heuristic: if spaces, assumes query
    is_query = " " in table_or_query.strip()
    source = f"({table_or_query})" if is_query else table_or_query
    
    try:
        con.execute(f"COPY {source} TO '{file_path}' (HEADER, DELIMITER ',')")
        return f"Exported to {file_path}"
    except Exception as e:
        return f"Error: {e}"

def export_parquet(table_or_query: str, file_path: str) -> str:
    """Save table/query to Parquet."""
    con = core_ops.get_connection()
    is_query = " " in table_or_query.strip()
    source = f"({table_or_query})" if is_query else table_or_query
    
    try:
        con.execute(f"COPY {source} TO '{file_path}' (FORMAT PARQUET)")
        return f"Exported to {file_path}"
    except Exception as e:
        return f"Error: {e}"

def export_json(table_or_query: str, file_path: str) -> str:
    """Save table/query to JSON."""
    con = core_ops.get_connection()
    is_query = " " in table_or_query.strip()
    source = f"({table_or_query})" if is_query else table_or_query
    
    try:
        con.execute(f"COPY {source} TO '{file_path}' (FORMAT JSON, ARRAY true)")
        return f"Exported to {file_path}"
    except Exception as e:
        return f"Error: {e}"

def copy_table(source_table: str, new_table: str) -> str:
    """Duplicate table structure+data."""
    con = core_ops.get_connection()
    try:
        con.execute(f"CREATE TABLE {new_table} AS SELECT * FROM {source_table}")
        return f"Copied {source_table} to {new_table}."
    except Exception as e:
        return f"Error: {e}"

def append_from_csv(table_name: str, file_path: str) -> str:
    """INSERT into existing table from CSV."""
    con = core_ops.get_connection()
    try:
        con.execute(f"INSERT INTO {table_name} SELECT * FROM read_csv('{file_path}')")
        return f"Appended data from {file_path} to {table_name}."
    except Exception as e:
        return f"Error: {e}"

def read_csv_as_view(file_path: str, view_name: str) -> str:
    """Create temporary view from CSV (no copy)."""
    con = core_ops.get_connection()
    try:
        con.execute(f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM read_csv('{file_path}')")
        return f"View {view_name} created for {file_path}."
    except Exception as e:
        return f"Error: {e}"

def read_parquet_as_view(file_path: str, view_name: str) -> str:
    """Create temporary view from Parquet."""
    con = core_ops.get_connection()
    try:
        con.execute(f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM read_parquet('{file_path}')")
        return f"View {view_name} created for {file_path}."
    except Exception as e:
        return f"Error: {e}"
