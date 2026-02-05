from mcp_servers.duckdb_server.tools import core_ops
from typing import Dict, Any, List

def time_bucket(table_name: str, time_col: str, interval: str, agg_col: str = "count(*)") -> List[Dict[str, Any]]:
    """Truncate timestamp to interval (1h, 15m) and aggregate."""
    con = core_ops.get_connection()
    try:
        # time_bucket('1 hour', time)
        query = f"""
        SELECT time_bucket(INTERVAL '{interval}', {time_col}) as bucket, {agg_col} as value
        FROM {table_name}
        GROUP BY bucket
        ORDER BY bucket
        """
        df = con.execute(query).df()
        # Convert timestamps to string
        df['bucket'] = df['bucket'].astype(str)
        return df.to_dict(orient="records")
    except Exception as e:
        return [{"error": str(e)}]

def gap_fill(table_name: str, time_col: str, interval: str, value_col: str) -> str:
    """Reference query logic for gap filling (not a direct tool execution usually)."""
    return "Gap filling requires generating a series and joining. Use `SELECT generate_series(...)` LEFT JOIN table."

def asof_join(table_a: str, table_b: str, time_col: str, join_col: str) -> str:
    """Perform ASOF JOIN (nearest timestamp). ASOF JOIN syntax."""
    # SELECT * FROM A ASOF JOIN B USING (join_col, time_col)?
    # DuckDB ASOF JOIN syntax: 
    # FROM a ASOF JOIN b ON a.id = b.id AND a.time >= b.time
    return "ASOF JOIN syntax: `SELECT * FROM table_a ASOF JOIN table_b ON ...` Use execute_query."

def lead_lag(table_name: str, col: str, order_col: str) -> List[Dict[str, Any]]:
    """Calculate lead/lag values."""
    con = core_ops.get_connection()
    try:
        query = f"""
        SELECT {col}, 
               LAG({col}) OVER (ORDER BY {order_col}) as prev_val,
               LEAD({col}) OVER (ORDER BY {order_col}) as next_val
        FROM {table_name}
        LIMIT 50
        """
        df = con.execute(query).df()
        return df.to_dict(orient="records")
    except Exception as e:
        return [{"error": str(e)}]

def moving_average(table_name: str, value_col: str, order_col: str, window: int) -> List[Dict[str, Any]]:
    """Moving average (AVG OVER ROWS BETWEEN N PRECEDING...)."""
    con = core_ops.get_connection()
    try:
        query = f"""
        SELECT {order_col}, {value_col},
               AVG({value_col}) OVER (ORDER BY {order_col} ROWS BETWEEN {window} PRECEDING AND CURRENT ROW) as moving_avg
        FROM {table_name}
        LIMIT 100
        """
        df = con.execute(query).df()
        return df.to_dict(orient="records")
    except Exception as e:
        return [{"error": str(e)}]

def date_diff(unit: str, start: str, end: str) -> int:
    """Difference between dates (test helper). date_diff('day', t1, t2)."""
    con = core_ops.get_connection()
    try:
        res = con.execute(f"SELECT date_diff('{unit}', CAST('{start}' AS DATE), CAST('{end}' AS DATE))").fetchone()
        return res[0]
    except Exception as e:
        return -1

def date_trunc(part: str, date: str) -> str:
    """Truncate date."""
    con = core_ops.get_connection()
    try:
        res = con.execute(f"SELECT date_trunc('{part}', CAST('{date}' AS TIMESTAMP))").fetchone()
        return str(res[0])
    except Exception as e:
        return str(e)

def make_timestamp(year: int, month: int, day: int, hour: int, min: int, sec: float) -> str:
    """Construct timestamp."""
    con = core_ops.get_connection()
    try:
        res = con.execute(f"SELECT make_timestamp({year}, {month}, {day}, {hour}, {min}, {sec})").fetchone()
        return str(res[0])
    except Exception as e:
        return str(e)
