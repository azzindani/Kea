import duckdb
from mcp_servers.duckdb_server.tools import core_ops
from typing import List, Dict, Any, Optional

def execute_query(query: str) -> str:
    """Run arbitrary SQL (INSERT/UPDATE/DELETE)."""
    con = core_ops.get_connection()
    try:
        con.execute(query)
        # Check if it was a select or modification
        # If no result set, return success message
        return "Query executed successfully."
    except Exception as e:
        return f"Error executing query: {e}"

def fetch_all(query: str) -> List[Dict[str, Any]]:
    """Run SELECT and return all rows (list of dicts)."""
    con = core_ops.get_connection()
    try:
        # fetchdf or fetcharrow is strictly typed, but fetchall returns tuples.
        # We want dicts for JSON output.
        # .df() then to_dict? 
        df = con.execute(query).df()
        # Handle timestamps/NaNs for JSON serialization safety if needed
        # Filling NaNs
        df = df.fillna("NULL") # simplified
        return df.to_dict(orient="records")
    except Exception as e:
        return [{"error": str(e)}]

def fetch_one(query: str) -> Dict[str, Any]:
    """Run SELECT and return one row."""
    con = core_ops.get_connection()
    try:
        df = con.execute(query).df()
        if df.empty: return {}
        df = df.fillna("NULL")
        return df.iloc[0].to_dict()
    except Exception as e:
        return {"error": str(e)}

def explain_query(query: str) -> str:
    """Show query plan."""
    con = core_ops.get_connection()
    try:
        # EXPLAIN ...
        return con.execute(f"EXPLAIN {query}").fetchall()[0][1] # usually 2nd col is plan
    except Exception as e:
        return f"Error explaining: {e}"

def count_rows(table_name: str) -> int:
    """SELECT COUNT(*) FROM table."""
    con = core_ops.get_connection()
    try:
        res = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        return res[0] if res else 0
    except:
        return -1

def get_table_schema(table_name: str) -> List[Dict[str, str]]:
    """Describe columns/types."""
    con = core_ops.get_connection()
    try:
        # DESCRIBE table
        res = con.execute(f"DESCRIBE {table_name}").fetchall()
        # format: column_name, column_type, null, key, default, extra
        schema = []
        for r in res:
            schema.append({
                "column": r[0],
                "type": r[1],
                "nullable": r[2] if len(r)>2 else "?"
            })
        return schema
    except Exception as e:
        return [{"error": str(e)}]

def list_tables() -> List[str]:
    """Show all tables in DB."""
    con = core_ops.get_connection()
    try:
        # SHOW TABLES
        res = con.execute("SHOW TABLES").fetchall()
        return [r[0] for r in res]
    except Exception as e:
        return [f"Error: {e}"]

def list_views() -> List[str]:
    """Show all views."""
    con = core_ops.get_connection()
    try:
        # specific query for views
        q = "SELECT table_name FROM information_schema.tables WHERE table_type='VIEW'"
        res = con.execute(q).fetchall()
        return [r[0] for r in res]
    except Exception as e:
        return [f"Error: {e}"]

def check_table_exists(table_name: str) -> bool:
    """Boolean check."""
    tables = list_tables()
    return table_name in tables

def preview_table(table_name: str, limit: int = 5) -> List[Dict[str, Any]]:
    """SELECT * LIMIT N."""
    return fetch_all(f"SELECT * FROM {table_name} LIMIT {limit}")
