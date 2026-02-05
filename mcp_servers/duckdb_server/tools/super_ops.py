from mcp_servers.duckdb_server.tools import core_ops
import os

def etl_pipeline_csv(input_csv: str, output_parquet: str, filter_sql: str = "1=1") -> str:
    """Load CSV -> Filter -> Save Parquet."""
    con = core_ops.get_connection()
    try:
        query = f"COPY (SELECT * FROM read_csv('{input_csv}', auto_detect=true) WHERE {filter_sql}) TO '{output_parquet}' (FORMAT PARQUET)"
        con.execute(query)
        return f"ETL complete: {input_csv} -> Filter -> {output_parquet}"
    except Exception as e:
        return f"Error: {e}"

def merge_tables(table_a: str, table_b: str, join_col: str, output_table: str, join_type: str = "INNER") -> str:
    """Join two tables and save as new table."""
    con = core_ops.get_connection()
    try:
        query = f"CREATE TABLE {output_table} AS SELECT * FROM {table_a} {join_type} JOIN {table_b} USING ({join_col})"
        con.execute(query)
        return f"Merged {table_a} and {table_b} into {output_table}."
    except Exception as e:
        return f"Error: {e}"

def query_remote_file(url: str, query_sql: str) -> str:
    """Query URL (CSV/Parquet) directly. `query_sql` should use 'tbl' as placeholder or just be full query using URL."""
    con = core_ops.get_connection()
    try:
        # Ensure httpfs is loaded
        con.execute("INSTALL httpfs; LOAD httpfs;")
        
        # If user provides simple SELECT * FROM tbl... we replace tbl with read_parquet(url)
        # Or assumes users knows to write SELECT * FROM read_parquet('https://...')
        # Let's support both. If query doesn't contain the url, assumes "FROM ?"
        
        final_query = query_sql
        if "read_" not in query_sql and "http" not in query_sql:
            # Assume query is a WHERE clause or full SELECT on implicit table
            if query_sql.strip().lower().startswith("select"):
                 # replace 'from tbl' isn't easy without parser.
                 # Let's just execute raw.
                 pass
            else:
                 pass
        
        # Simpler: User provides URL and a SQL like "SELECT count(*) FROM ?"
        # We replace ? with read_parquet('url') or read_csv('url') based on extension
        if "?" in query_sql:
             func = "read_parquet" if ".parquet" in url else "read_csv"
             source = f"{func}('{url}')"
             final_query = query_sql.replace("?", source)
        
        df = con.execute(final_query).df()
        return df.to_markdown(index=False)
    except Exception as e:
        return f"Error: {e}"

def diff_tables(table_a: str, table_b: str, key_col: str) -> str:
    """Find rows in A but not B (Anti Join)."""
    con = core_ops.get_connection()
    try:
        query = f"SELECT * FROM {table_a} WHERE {key_col} NOT IN (SELECT {key_col} FROM {table_b})"
        df = con.execute(query).df()
        return df.to_markdown(index=False)
    except Exception as e:
        return f"Error: {e}"

def sample_table(table_name: str, sample_size: int, output_table: str) -> str:
    """Create a random sample (N rows) new table."""
    con = core_ops.get_connection()
    try:
        query = f"CREATE TABLE {output_table} AS SELECT * FROM {table_name} USING SAMPLE {sample_size} ROWS"
        con.execute(query)
        return f"Sampled {sample_size} rows from {table_name} to {output_table}."
    except Exception as e:
        return f"Error: {e}"

def data_quality_report(table_name: str) -> str:
    """Run multiple checks (nulls, unique count)."""
    con = core_ops.get_connection()
    try:
        # Basic profile using SUMMARIZE
        df = con.execute(f"SUMMARIZE {table_name}").df()
        return df.to_markdown()
    except Exception as e:
        return f"Error: {e}"

def convert_file_format(input_file: str, output_file: str) -> str:
    """Universal converter (CSV key-> Parquet, JSON -> CSV)."""
    con = core_ops.get_connection()
    try:
        # Infer read func from input, save format from output
        # DuckDB usually infers from extension in simple COPY ... FROM ...
        # But COPY ... FROM 'file' not supported directly for all formats in one go same as read
        
        # Use query approach
        read_func = "read_csv"
        if input_file.lower().endswith(".parquet"): read_func = "read_parquet"
        if input_file.lower().endswith(".json"): read_func = "read_json"
        
        format_opts = ""
        if output_file.lower().endswith(".parquet"): format_opts = "(FORMAT PARQUET)"
        if output_file.lower().endswith(".json"): format_opts = "(FORMAT JSON, ARRAY true)"
        if output_file.lower().endswith(".csv"): format_opts = "(HEADER, DELIMITER ',')"
        
        query = f"COPY (SELECT * FROM {read_func}('{input_file}', auto_detect=true)) TO '{output_file}' {format_opts}"
        con.execute(query)
        return f"Converted {input_file} to {output_file}"
    except Exception as e:
        return f"Error: {e}"

def full_text_search(table_name: str, column_name: str, keyword: str) -> str:
    """Basic LIKE search (placeholder for FTS extension)."""
    con = core_ops.get_connection()
    try:
        query = f"SELECT * FROM {table_name} WHERE {column_name} LIKE '%{keyword}%' LIMIT 20"
        df = con.execute(query).df()
        return df.to_markdown(index=False)
    except Exception as e:
        return f"Error: {e}"
