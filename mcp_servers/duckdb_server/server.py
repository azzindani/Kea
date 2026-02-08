
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "duckdb",
#   "mcp",
#   "pandas",
#   "pyarrow",
#   "structlog",
# ]
# ///

from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.duckdb_server.tools import (
    core_ops, query_ops, schema_ops, io_ops, analysis_ops, super_ops,
    spatial_ops, text_ops, time_ops, infra_ops
)
import structlog
from typing import Dict, Any, Optional, List

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging import setup_logging
setup_logging()

mcp = FastMCP("duckdb_server", dependencies=["pandas", "duckdb", "pyarrow"])

# ==========================================
# 1. Core
# ==========================================
# ==========================================
# 1. Core
# ==========================================
@mcp.tool()
def connect_db(path: str = "kea_data.duckdb") -> str: 
    """CONNECTS to database. [ACTION]
    
    [RAG Context]
    Connect to DuckDB database file.
    Returns status string.
    """
    return core_ops.connect_db(path)

@mcp.tool()
def get_version() -> str: 
    """FETCHES version. [ACTION]
    
    [RAG Context]
    Get DuckDB version.
    Returns version string.
    """
    return core_ops.get_version()

@mcp.tool()
def list_extensions() -> str: 
    """LISTS extensions. [ACTION]
    
    [RAG Context]
    List installed/loaded extensions.
    Returns table string.
    """
    return core_ops.list_extensions()

@mcp.tool()
def install_extension(name: str) -> str: 
    """INSTALLS extension. [ACTION]
    
    [RAG Context]
    Install a DuckDB extension.
    Returns status string.
    """
    return core_ops.install_extension(name)

@mcp.tool()
def load_extension(name: str) -> str: 
    """LOADS extension. [ACTION]
    
    [RAG Context]
    Load a DuckDB extension.
    Returns status string.
    """
    return core_ops.load_extension(name)

@mcp.tool()
def get_current_db_path() -> str: 
    """FETCHES db path. [ACTION]
    
    [RAG Context]
    Get current database file path.
    Returns path string.
    """
    return core_ops.get_current_db_path()

@mcp.tool()
def close_connection() -> str: 
    """CLOSES connection. [ACTION]
    
    [RAG Context]
    Close current database connection.
    Returns status string.
    """
    return core_ops.close_connection()

@mcp.tool()
def set_config(key: str, value: str) -> str: 
    """SETS config. [ACTION]
    
    [RAG Context]
    Set DuckDB configuration option.
    Returns status string.
    """
    return core_ops.set_config(key, value)

# ==========================================
# 2. Query
# ==========================================
@mcp.tool()
def execute_query(query: str) -> str: 
    """EXECUTES SQL query. [ACTION]
    
    [RAG Context]
    Execute SQL query and return result as string.
    Returns table string.
    """
    return query_ops.execute_query(query)

@mcp.tool()
def fetch_all(query: str) -> List[Dict[str, Any]]: 
    """FETCHES all rows. [ACTION]
    
    [RAG Context]
    Execute SQL and return all rows as dicts.
    Returns list of dicts.
    """
    return query_ops.fetch_all(query)

@mcp.tool()
def fetch_one(query: str) -> Dict[str, Any]: 
    """FETCHES one row. [ACTION]
    
    [RAG Context]
    Execute SQL and return first row.
    Returns JSON dict.
    """
    return query_ops.fetch_one(query)

@mcp.tool()
def explain_query(query: str) -> str: 
    """EXPLAINS query plan. [ACTION]
    
    [RAG Context]
    Get execution plan for SQL query.
    Returns plan string.
    """
    return query_ops.explain_query(query)

@mcp.tool()
def count_rows(table_name: str) -> int: 
    """COUNTS rows. [ACTION]
    
    [RAG Context]
    Count rows in a table.
    Returns int.
    """
    return query_ops.count_rows(table_name)

@mcp.tool()
def get_table_schema(table_name: str) -> List[Dict[str, str]]: 
    """FETCHES schema. [ACTION]
    
    [RAG Context]
    Get column names and types for table.
    Returns list of dicts.
    """
    return query_ops.get_table_schema(table_name)

@mcp.tool()
def list_tables() -> List[str]: 
    """LISTS tables. [ACTION]
    
    [RAG Context]
    Get list of tables in database.
    Returns list of strings.
    """
    return query_ops.list_tables()

@mcp.tool()
def list_views() -> List[str]: 
    """LISTS views. [ACTION]
    
    [RAG Context]
    Get list of views in database.
    Returns list of strings.
    """
    return query_ops.list_views()

@mcp.tool()
def check_table_exists(table_name: str) -> bool: 
    """CHECKS table exists. [ACTION]
    
    [RAG Context]
    Check if table exists in database.
    Returns boolean.
    """
    return query_ops.check_table_exists(table_name)

@mcp.tool()
def preview_table(table_name: str, limit: int = 100000) -> List[Dict[str, Any]]: 
    """PREVIEWS table data. [ACTION]
    
    [RAG Context]
    Get first N rows of table.
    Returns list of dicts.
    """
    return query_ops.preview_table(table_name, limit)

# ==========================================
# 3. Schema
# ==========================================
# ==========================================
# 3. Schema
# ==========================================
@mcp.tool()
def create_table(table_name: str, columns: Dict[str, str]) -> str: 
    """CREATES table. [ACTION]
    
    [RAG Context]
    Create a new table with specified columns.
    Returns status string.
    """
    return schema_ops.create_table(table_name, columns)

@mcp.tool()
def drop_table(table_name: str) -> str: 
    """DROPS table. [ACTION]
    
    [RAG Context]
    Delete a table if it exists.
    Returns status string.
    """
    return schema_ops.drop_table(table_name)

@mcp.tool()
def alter_table_rename(old_name: str, new_name: str) -> str: 
    """RENAMES table. [ACTION]
    
    [RAG Context]
    Rename an existing table.
    Returns status string.
    """
    return schema_ops.alter_table_rename(old_name, new_name)

@mcp.tool()
def add_column(table_name: str, column_name: str, column_type: str) -> str: 
    """ADDS column. [ACTION]
    
    [RAG Context]
    Add a new column to a table.
    Returns status string.
    """
    return schema_ops.add_column(table_name, column_name, column_type)

@mcp.tool()
def create_index(index_name: str, table_name: str, column_name: str) -> str: 
    """CREATES index. [ACTION]
    
    [RAG Context]
    Create an index on a table column.
    Returns status string.
    """
    return schema_ops.create_index(index_name, table_name, column_name)

@mcp.tool()
def drop_index(index_name: str) -> str: 
    """DROPS index. [ACTION]
    
    [RAG Context]
    Delete an index.
    Returns status string.
    """
    return schema_ops.drop_index(index_name)

@mcp.tool()
def create_view(view_name: str, query: str) -> str: 
    """CREATES view. [ACTION]
    
    [RAG Context]
    Create a view from a SQL query.
    Returns status string.
    """
    return schema_ops.create_view(view_name, query)

@mcp.tool()
def drop_view(view_name: str) -> str: 
    """DROPS view. [ACTION]
    
    [RAG Context]
    Delete a view.
    Returns status string.
    """
    return schema_ops.drop_view(view_name)

@mcp.tool()
def truncate_table(table_name: str) -> str: 
    """TRUNCATES table. [ACTION]
    
    [RAG Context]
    Delete all rows from a table (keep schema).
    Returns status string.
    """
    return schema_ops.truncate_table(table_name)

# ==========================================
# 4. Import/Export
# ==========================================
@mcp.tool()
def import_csv(file_path: str, table_name: str, auto_detect: bool = True) -> str: 
    """IMPORTS CSV. [ACTION]
    
    [RAG Context]
    Load CSV file into a table.
    Returns status string.
    """
    return io_ops.import_csv(file_path, table_name, auto_detect)

@mcp.tool()
def import_parquet(file_path: str, table_name: str) -> str: 
    """IMPORTS Parquet. [ACTION]
    
    [RAG Context]
    Load Parquet file into a table.
    Returns status string.
    """
    return io_ops.import_parquet(file_path, table_name)

@mcp.tool()
def import_json(file_path: str, table_name: str, format: str = "auto") -> str: 
    """IMPORTS JSON. [ACTION]
    
    [RAG Context]
    Load JSON file into a table.
    Returns status string.
    """
    return io_ops.import_json(file_path, table_name, format)

@mcp.tool()
def export_csv(table_or_query: str, file_path: str) -> str: 
    """EXPORTS to CSV. [ACTION]
    
    [RAG Context]
    Save table or query result to CSV.
    Returns status string.
    """
    return io_ops.export_csv(table_or_query, file_path)

@mcp.tool()
def export_parquet(table_or_query: str, file_path: str) -> str: 
    """EXPORTS to Parquet. [ACTION]
    
    [RAG Context]
    Save table or query result to Parquet.
    Returns status string.
    """
    return io_ops.export_parquet(table_or_query, file_path)

@mcp.tool()
def export_json(table_or_query: str, file_path: str) -> str: 
    """EXPORTS to JSON. [ACTION]
    
    [RAG Context]
    Save table or query result to JSON.
    Returns status string.
    """
    return io_ops.export_json(table_or_query, file_path)

@mcp.tool()
def copy_table(source_table: str, new_table: str) -> str: 
    """COPIES table. [ACTION]
    
    [RAG Context]
    Duplicate a table.
    Returns status string.
    """
    return io_ops.copy_table(source_table, new_table)

@mcp.tool()
def append_from_csv(table_name: str, file_path: str) -> str: 
    """APPENDS from CSV. [ACTION]
    
    [RAG Context]
    Add rows from CSV to existing table.
    Returns status string.
    """
    return io_ops.append_from_csv(table_name, file_path)

@mcp.tool()
def read_csv_as_view(file_path: str, view_name: str) -> str: 
    """READS CSV as view. [ACTION]
    
    [RAG Context]
    Create view directly from CSV file (no copy).
    Returns status string.
    """
    return io_ops.read_csv_as_view(file_path, view_name)

@mcp.tool()
def read_parquet_as_view(file_path: str, view_name: str) -> str: 
    """READS Parquet as view. [ACTION]
    
    [RAG Context]
    Create view directly from Parquet file (no copy).
    Returns status string.
    """
    return io_ops.read_parquet_as_view(file_path, view_name)

# ==========================================
# 5. Analysis
# ==========================================
# ==========================================
# 5. Analysis
# ==========================================
@mcp.tool()
def get_column_stats(table_name: str, column_name: str) -> Dict[str, Any]: 
    """FETCHES column stats. [ACTION]
    
    [RAG Context]
    Get statistics (min, max, nulls) for a column.
    Returns JSON dict.
    """
    return analysis_ops.get_column_stats(table_name, column_name)

@mcp.tool()
def value_counts(table_name: str, column_name: str, limit: int = 100000) -> List[Dict[str, Any]]: 
    """CALCULATES value counts. [ACTION]
    
    [RAG Context]
    Count unique values in a column.
    Returns list of dicts.
    """
    return analysis_ops.value_counts(table_name, column_name, limit)

@mcp.tool()
def correlation_matrix(table_name: str, col1: str, col2: str) -> float: 
    """CALCULATES correlation. [ACTION]
    
    [RAG Context]
    Compute correlation between two columns.
    Returns float.
    """
    return analysis_ops.correlation_matrix(table_name, col1, col2)

@mcp.tool()
def percentiles(table_name: str, column_name: str) -> Dict[str, float]: 
    """CALCULATES percentiles. [ACTION]
    
    [RAG Context]
    Get 25th, 50th, 75th percentiles.
    Returns JSON dict.
    """
    return analysis_ops.percentiles(table_name, column_name)

@mcp.tool()
def detect_outliers_zscore(table_name: str, column_name: str, threshold: float = 3.0) -> List[Dict[str, Any]]: 
    """DETECTS outliers (Z-Score). [ACTION]
    
    [RAG Context]
    Find rows with Z-Score > threshold.
    Returns list of outliers.
    """
    return analysis_ops.detect_outliers_zscore(table_name, column_name, threshold)

@mcp.tool()
def summarize_table(table_name: str) -> str: 
    """SUMMARIZES table. [ACTION]
    
    [RAG Context]
    Get comprehensive table summary.
    Returns text report.
    """
    return analysis_ops.summarize_table(table_name)

@mcp.tool()
def pivot_table(table_name: str, index_col: str, pivot_col: str, value_col: str, agg_func: str = "SUM") -> List[Dict[str, Any]]: 
    """CREATES pivot table. [ACTION]
    
    [RAG Context]
    Reshape data (pivot) with aggregation.
    Returns list of dicts.
    """
    return analysis_ops.pivot_table(table_name, index_col, pivot_col, value_col, agg_func)

# ==========================================
# 6. Super Tools
# ==========================================
# ==========================================
# 6. Super Tools
# ==========================================
@mcp.tool()
def etl_pipeline_csv(input_csv: str, output_parquet: str, filter_sql: str = "1=1") -> str: 
    """RUNS ETL pipeline. [ACTION]
    
    [RAG Context]
    Extract CSV, Transform (filter), Load Parquet.
    Returns status string.
    """
    return super_ops.etl_pipeline_csv(input_csv, output_parquet, filter_sql)

@mcp.tool()
def merge_tables(table_a: str, table_b: str, join_col: str, output_table: str, join_type: str = "INNER") -> str: 
    """MERGES tables. [ACTION]
    
    [RAG Context]
    Join two tables into a new table.
    Returns status string.
    """
    return super_ops.merge_tables(table_a, table_b, join_col, output_table, join_type)

@mcp.tool()
def query_remote_file(url: str, query_sql: str) -> str: 
    """QUERIES remote file. [ACTION]
    
    [RAG Context]
    Query a remote Parquet/CSV/JSON file directly.
    Returns table string.
    """
    return super_ops.query_remote_file(url, query_sql)

@mcp.tool()
def diff_tables(table_a: str, table_b: str, key_col: str) -> str: 
    """DIFFS tables. [ACTION]
    
    [RAG Context]
    Find differences between two tables.
    Returns table string (diff rows).
    """
    return super_ops.diff_tables(table_a, table_b, key_col)

@mcp.tool()
def sample_table(table_name: str, sample_size: int, output_table: str) -> str: 
    """SAMPLES table. [ACTION]
    
    [RAG Context]
    Create a random sample of a table.
    Returns status string.
    """
    return super_ops.sample_table(table_name, sample_size, output_table)

@mcp.tool()
def data_quality_report(table_name: str) -> str: 
    """GENERATES quality report. [ACTION]
    
    [RAG Context]
    Check for nulls, duplicates, and constraints.
    Returns report string.
    """
    return super_ops.data_quality_report(table_name)

@mcp.tool()
def convert_file_format(input_file: str, output_file: str) -> str: 
    """CONVERTS file format. [ACTION]
    
    [RAG Context]
    Convert between CSV, Parquet, JSON.
    Returns status string.
    """
    return super_ops.convert_file_format(input_file, output_file)

@mcp.tool()
def full_text_search(table_name: str, column_name: str, keyword: str) -> str: 
    """SEARCHES text. [ACTION]
    
    [RAG Context]
    Search for keyword in text column.
    Returns table string.
    """
    return super_ops.full_text_search(table_name, column_name, keyword)

# ==========================================
# 7. Spatial
# ==========================================
# ==========================================
# 7. Spatial
# ==========================================
@mcp.tool()
def st_point(lat: float, lon: float) -> str: 
    """CREATES point. [ACTION]
    
    [RAG Context]
    Create a spatial point from lat/lon.
    Returns WKT string.
    """
    return spatial_ops.st_point(lat, lon)

@mcp.tool()
def st_distance(wkt_a: str, wkt_b: str) -> float: 
    """CALCULATES spatial dist. [ACTION]
    
    [RAG Context]
    Compute distance between two geometries.
    Returns float.
    """
    return spatial_ops.st_distance(wkt_a, wkt_b)

@mcp.tool()
def st_area(wkt_poly: str) -> float: 
    """CALCULATES area. [ACTION]
    
    [RAG Context]
    Compute area of a polygon.
    Returns float.
    """
    return spatial_ops.st_area(wkt_poly)

@mcp.tool()
def st_contains(wkt_a: str, wkt_b: str) -> bool: 
    """CHECKS containment. [ACTION]
    
    [RAG Context]
    Check if geometry A contains geometry B.
    Returns boolean.
    """
    return spatial_ops.st_contains(wkt_a, wkt_b)

@mcp.tool()
def st_intersects(wkt_a: str, wkt_b: str) -> bool: 
    """CHECKS intersection. [ACTION]
    
    [RAG Context]
    Check if geometry A intersects geometry B.
    Returns boolean.
    """
    return spatial_ops.st_intersects(wkt_a, wkt_b)

@mcp.tool()
def st_buffer(wkt_geom: str, dist: float) -> str: 
    """CREATES buffer. [ACTION]
    
    [RAG Context]
    Create specific distance buffer around geometry.
    Returns WKT string.
    """
    return spatial_ops.st_buffer(wkt_geom, dist)

@mcp.tool()
def st_centroid(wkt_geom: str) -> str: 
    """CALCULATES centroid. [ACTION]
    
    [RAG Context]
    Get center point of geometry.
    Returns WKT string.
    """
    return spatial_ops.st_centroid(wkt_geom)

@mcp.tool()
def st_read(file_path: str, table_name: str) -> str: 
    """READS spatial file. [ACTION]
    
    [RAG Context]
    Load Shapefile, GeoJSON, etc into table.
    Returns status string.
    """
    return spatial_ops.st_read(file_path, table_name)

@mcp.tool()
def st_as_text(wkb_col: str, table_name: str) -> List[str]: 
    """CONVERTS to WKT. [ACTION]
    
    [RAG Context]
    Convert binary geometry to Text (WKT).
    Returns list of strings.
    """
    return spatial_ops.st_as_text(wkb_col, table_name)

@mcp.tool()
def st_as_geojson(wkt_geom: str) -> str: 
    """CONVERTS to GeoJSON. [ACTION]
    
    [RAG Context]
    Convert WKT geometry to GeoJSON.
    Returns GeoJSON string.
    """
    return spatial_ops.st_as_geojson(wkt_geom)

# ==========================================
# 8. Text & JSON
# ==========================================
# ==========================================
# 8. Text & JSON
# ==========================================
@mcp.tool()
def fts_create_index(table_name: str, id_col: str, text_cols: List[str]) -> str: 
    """CREATES FTS index. [ACTION]
    
    [RAG Context]
    Create Full Text Search index on table.
    Returns status string.
    """
    return text_ops.fts_create_index(table_name, id_col, text_cols)

@mcp.tool()
def fts_search(table_name: str, keyword: str, limit: int = 100000) -> List[Dict[str, Any]]: 
    """SEARCHES FTS. [ACTION]
    
    [RAG Context]
    Search using existing FTS index.
    Returns list of matches.
    """
    return text_ops.fts_search(table_name, keyword, limit)

@mcp.tool()
def json_extract_path(table_name: str, json_col: str, path: str) -> List[Any]: 
    """EXTRACTS JSON path. [ACTION]
    
    [RAG Context]
    Extract value from JSON column by path.
    Returns list of values.
    """
    return text_ops.json_extract_path(table_name, json_col, path)

@mcp.tool()
def json_create(keys: List[str], values: List[Any]) -> str: 
    """CREATES JSON. [ACTION]
    
    [RAG Context]
    Create JSON object from keys and values.
    Returns JSON string.
    """
    return text_ops.json_create(keys, values)

@mcp.tool()
def regexp_extract(text: str, pattern: str) -> str: 
    """EXTRACTS regex. [ACTION]
    
    [RAG Context]
    Extract substring matching regex.
    Returns string.
    """
    return text_ops.regexp_extract(text, pattern)

@mcp.tool()
def regexp_matches(text: str, pattern: str) -> bool: 
    """CHECKS regex match. [ACTION]
    
    [RAG Context]
    Check if text matches regex pattern.
    Returns boolean.
    """
    return text_ops.regexp_matches(text, pattern)

@mcp.tool()
def read_json_objects(file_path: str) -> List[Dict[str, Any]]: 
    """READS JSON objects. [ACTION]
    
    [RAG Context]
    Read newline-delimited JSON objects.
    Returns list of dicts.
    """
    return text_ops.read_json_objects(file_path)

# ==========================================
# 9. Time Series
# ==========================================
# ==========================================
# 9. Time Series
# ==========================================
@mcp.tool()
def time_bucket(table_name: str, time_col: str, interval: str, agg_col: str = "count(*)") -> List[Dict[str, Any]]: 
    """BUCKETS time. [ACTION]
    
    [RAG Context]
    Group data by time interval (e.g., '1 day').
    Returns list of dicts.
    """
    return time_ops.time_bucket(table_name, time_col, interval, agg_col)

@mcp.tool()
def gap_fill(table_name: str, time_col: str, interval: str, value_col: str) -> str: 
    """FILLS time gaps. [ACTION]
    
    [RAG Context]
    Fill missing time buckets with previous value.
    Returns status string.
    """
    return time_ops.gap_fill(table_name, time_col, interval, value_col)

@mcp.tool()
def asof_join(table_a: str, table_b: str, time_col: str, join_col: str) -> str: 
    """JOINS as-of. [ACTION]
    
    [RAG Context]
    Join on nearest time key (ASOF join).
    Returns status string.
    """
    return time_ops.asof_join(table_a, table_b, time_col, join_col)

@mcp.tool()
def lead_lag(table_name: str, col: str, order_col: str) -> List[Dict[str, Any]]: 
    """CALCULATES lead/lag. [ACTION]
    
    [RAG Context]
    Compute lead and lag values for a column.
    Returns list of dicts.
    """
    return time_ops.lead_lag(table_name, col, order_col)

@mcp.tool()
def moving_average(table_name: str, value_col: str, order_col: str, window: int) -> List[Dict[str, Any]]: 
    """CALCULATES moving avg. [ACTION]
    
    [RAG Context]
    Compute simple moving average.
    Returns list of dicts.
    """
    return time_ops.moving_average(table_name, value_col, order_col, window)

@mcp.tool()
def date_diff(unit: str, start: str, end: str) -> int: 
    """CALCULATES date diff. [ACTION]
    
    [RAG Context]
    Difference between two dates in unit.
    Returns integer.
    """
    return time_ops.date_diff(unit, start, end)

@mcp.tool()
def date_trunc(part: str, date: str) -> str: 
    """TRUNCATES date. [ACTION]
    
    [RAG Context]
    Truncate date to specified precision.
    Returns date string.
    """
    return time_ops.date_trunc(part, date)

@mcp.tool()
def make_timestamp(year: int, month: int, day: int, hour: int, min: int, sec: float) -> str: 
    """CREATES timestamp. [ACTION]
    
    [RAG Context]
    Construct timestamp from parts.
    Returns timestamp string.
    """
    return time_ops.make_timestamp(year, month, day, hour, min, sec)

# ==========================================
# 10. Infra
# ==========================================
@mcp.tool()
def parquet_metadata(file_path: str) -> str: 
    """FETCHES Parquet metadata. [ACTION]
    
    [RAG Context]
    Get metadata from Parquet file (no load).
    Returns metadata string.
    """
    return infra_ops.parquet_metadata(file_path)

@mcp.tool()
def parquet_schema(file_path: str) -> str: 
    """FETCHES Parquet schema. [ACTION]
    
    [RAG Context]
    Get schema from Parquet file (no load).
    Returns schema string.
    """
    return infra_ops.parquet_schema(file_path)

@mcp.tool()
def current_db_size() -> str: 
    """FETCHES DB size. [ACTION]
    
    [RAG Context]
    Get size of current database file.
    Returns size string.
    """
    return infra_ops.current_db_size()

@mcp.tool()
def show_tables_expanded() -> str: 
    """LISTS tables detailed. [ACTION]
    
    [RAG Context]
    Get detailed list of tables (size, row count).
    Returns table string.
    """
    return infra_ops.show_tables_expanded()

@mcp.tool()
def describe_table_detailed(table_name: str) -> str: 
    """DESCRIBES table detailed. [ACTION]
    
    [RAG Context]
    Get detailed schema and stats for table.
    Returns report string.
    """
    return infra_ops.describe_table_detailed(table_name)

@mcp.tool()
def get_memory_usage() -> str: 
    """FETCHES memory usage. [ACTION]
    
    [RAG Context]
    Get DuckDB memory usage stats.
    Returns stats string.
    """
    return infra_ops.get_memory_usage()

@mcp.tool()
def list_settings() -> str: 
    """LISTS settings. [ACTION]
    
    [RAG Context]
    List all DuckDB configuration settings.
    Returns table string.
    """
    return infra_ops.list_settings()

@mcp.tool()
def checkpoint_db() -> str: 
    """CHECKPOINTS database. [ACTION]
    
    [RAG Context]
    Force a checkpoint of the WAL.
    Returns status string.
    """
    return infra_ops.checkpoint_db()

@mcp.tool()
def vacuum_db() -> str: 
    """VACUUMS database. [ACTION]
    
    [RAG Context]
    Reclaim unused space in database.
    Returns status string.
    """
    return infra_ops.vacuum_db()

@mcp.tool()
def get_query_profiling(query: str) -> str: 
    """PROFILES query. [ACTION]
    
    [RAG Context]
    Run query and return profiling info.
    Returns profile string.
    """
    return infra_ops.get_query_profiling(query)

if __name__ == "__main__":
    mcp.run()