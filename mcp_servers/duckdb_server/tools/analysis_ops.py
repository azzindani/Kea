from mcp_servers.duckdb_server.tools import core_ops
from typing import Dict, Any, List

def get_column_stats(table_name: str, column_name: str) -> Dict[str, Any]:
    """Min, Max, Avg, Null Count for column."""
    con = core_ops.get_connection()
    try:
        query = f"SELECT MIN({column_name}), MAX({column_name}), AVG({column_name}), COUNT(*) - COUNT({column_name}) as nulls FROM {table_name}"
        res = con.execute(query).fetchone()
        return {
            "min": res[0],
            "max": res[1],
            "avg": res[2],
            "null_count": res[3]
        }
    except Exception as e:
        return {"error": str(e)}

def value_counts(table_name: str, column_name: str, limit: int = 20) -> List[Dict[str, Any]]:
    """GROUP BY column COUNT(*)."""
    con = core_ops.get_connection()
    try:
        query = f"SELECT {column_name}, COUNT(*) as count FROM {table_name} GROUP BY {column_name} ORDER BY count DESC LIMIT {limit}"
        df = con.execute(query).df()
        return df.to_dict(orient="records")
    except Exception as e:
        return [{"error": str(e)}]

def correlation_matrix(table_name: str, col1: str, col2: str) -> float:
    """Correlation between two numeric columns."""
    con = core_ops.get_connection()
    try:
        res = con.execute(f"SELECT corr({col1}, {col2}) FROM {table_name}").fetchone()
        return res[0]
    except Exception as e:
        return 0.0

def percentiles(table_name: str, column_name: str) -> Dict[str, float]:
    """Calculate p25, p50, p75, p90, p99."""
    con = core_ops.get_connection()
    try:
        query = f"SELECT quantile_cont({column_name}, [0.25, 0.5, 0.75, 0.9, 0.99]) FROM {table_name}"
        res = con.execute(query).fetchone()[0] # returns list
        return {
            "p25": res[0],
            "p50": res[1],
            "p75": res[2],
            "p90": res[3],
            "p99": res[4]
        }
    except Exception as e:
        return {"error": str(e)}

def detect_outliers_zscore(table_name: str, column_name: str, threshold: float = 3.0) -> List[Dict[str, Any]]:
    """Find rows > threshold std devs."""
    con = core_ops.get_connection()
    try:
        # CTE to calc stats, then filter
        query = f"""
        WITH stats AS (
            SELECT AVG({column_name}) as mean, STDDEV({column_name}) as sd FROM {table_name}
        )
        SELECT * FROM {table_name}, stats
        WHERE ABS(({column_name} - mean) / sd) > {threshold}
        LIMIT 100
        """
        df = con.execute(query).df()
        return df.to_dict(orient="records")
    except Exception as e:
        return [{"error": str(e)}]

def summarize_table(table_name: str) -> str:
    """SUMMARIZE statement result (summary stats for all cols)."""
    con = core_ops.get_connection()
    try:
        # SUMMARIZE returns a table result, let's return it as markdown text or generic json
        df = con.execute(f"SUMMARIZE {table_name}").df()
        return df.to_markdown(index=False)
    except Exception as e:
        return f"Error: {e}"

def pivot_table(table_name: str, index_col: str, pivot_col: str, value_col: str, agg_func: str = "SUM") -> List[Dict[str, Any]]:
    """Pivot/crosstab query helper."""
    con = core_ops.get_connection()
    try:
        # PIVOT {on} USING {agg} GROUP BY {rows}
        query = f"PIVOT {table_name} ON {pivot_col} USING {agg_func}({value_col}) GROUP BY {index_col}"
        df = con.execute(query).df()
        return df.to_dict(orient="records")
    except Exception as e:
        return [{"error": str(e)}]
