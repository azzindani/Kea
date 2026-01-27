from mcp.server.fastmcp import FastMCP
from mcp_servers.duckdb_server.tools import (
    core_ops, query_ops, schema_ops, io_ops, analysis_ops, super_ops,
    spatial_ops, text_ops, time_ops, infra_ops
)
import structlog
from typing import Dict, Any, Optional, List

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("duckdb_server", dependencies=["pandas", "duckdb", "pyarrow"])

# ==========================================
# 1. Core
# ==========================================
@mcp.tool()
def connect_db(path: str = "kea_data.duckdb") -> str: return core_ops.connect_db(path)
@mcp.tool()
def get_version() -> str: return core_ops.get_version()
@mcp.tool()
def list_extensions() -> str: return core_ops.list_extensions()
@mcp.tool()
def install_extension(name: str) -> str: return core_ops.install_extension(name)
@mcp.tool()
def load_extension(name: str) -> str: return core_ops.load_extension(name)
@mcp.tool()
def get_current_db_path() -> str: return core_ops.get_current_db_path()
@mcp.tool()
def close_connection() -> str: return core_ops.close_connection()
@mcp.tool()
def set_config(key: str, value: str) -> str: return core_ops.set_config(key, value)

# ==========================================
# 2. Query
# ==========================================
@mcp.tool()
def execute_query(query: str) -> str: return query_ops.execute_query(query)
@mcp.tool()
def fetch_all(query: str) -> List[Dict[str, Any]]: return query_ops.fetch_all(query)
@mcp.tool()
def fetch_one(query: str) -> Dict[str, Any]: return query_ops.fetch_one(query)
@mcp.tool()
def explain_query(query: str) -> str: return query_ops.explain_query(query)
@mcp.tool()
def count_rows(table_name: str) -> int: return query_ops.count_rows(table_name)
@mcp.tool()
def get_table_schema(table_name: str) -> List[Dict[str, str]]: return query_ops.get_table_schema(table_name)
@mcp.tool()
def list_tables() -> List[str]: return query_ops.list_tables()
@mcp.tool()
def list_views() -> List[str]: return query_ops.list_views()
@mcp.tool()
def check_table_exists(table_name: str) -> bool: return query_ops.check_table_exists(table_name)
@mcp.tool()
def preview_table(table_name: str, limit: int = 5) -> List[Dict[str, Any]]: return query_ops.preview_table(table_name, limit)

# ==========================================
# 3. Schema
# ==========================================
@mcp.tool()
def create_table(table_name: str, columns: Dict[str, str]) -> str: return schema_ops.create_table(table_name, columns)
@mcp.tool()
def drop_table(table_name: str) -> str: return schema_ops.drop_table(table_name)
@mcp.tool()
def alter_table_rename(old_name: str, new_name: str) -> str: return schema_ops.alter_table_rename(old_name, new_name)
@mcp.tool()
def add_column(table_name: str, column_name: str, column_type: str) -> str: return schema_ops.add_column(table_name, column_name, column_type)
@mcp.tool()
def create_index(index_name: str, table_name: str, column_name: str) -> str: return schema_ops.create_index(index_name, table_name, column_name)
@mcp.tool()
def drop_index(index_name: str) -> str: return schema_ops.drop_index(index_name)
@mcp.tool()
def create_view(view_name: str, query: str) -> str: return schema_ops.create_view(view_name, query)
@mcp.tool()
def drop_view(view_name: str) -> str: return schema_ops.drop_view(view_name)
@mcp.tool()
def truncate_table(table_name: str) -> str: return schema_ops.truncate_table(table_name)

# ==========================================
# 4. Import/Export
# ==========================================
@mcp.tool()
def import_csv(file_path: str, table_name: str, auto_detect: bool = True) -> str: return io_ops.import_csv(file_path, table_name, auto_detect)
@mcp.tool()
def import_parquet(file_path: str, table_name: str) -> str: return io_ops.import_parquet(file_path, table_name)
@mcp.tool()
def import_json(file_path: str, table_name: str, format: str = "auto") -> str: return io_ops.import_json(file_path, table_name, format)
@mcp.tool()
def export_csv(table_or_query: str, file_path: str) -> str: return io_ops.export_csv(table_or_query, file_path)
@mcp.tool()
def export_parquet(table_or_query: str, file_path: str) -> str: return io_ops.export_parquet(table_or_query, file_path)
@mcp.tool()
def export_json(table_or_query: str, file_path: str) -> str: return io_ops.export_json(table_or_query, file_path)
@mcp.tool()
def copy_table(source_table: str, new_table: str) -> str: return io_ops.copy_table(source_table, new_table)
@mcp.tool()
def append_from_csv(table_name: str, file_path: str) -> str: return io_ops.append_from_csv(table_name, file_path)
@mcp.tool()
def read_csv_as_view(file_path: str, view_name: str) -> str: return io_ops.read_csv_as_view(file_path, view_name)
@mcp.tool()
def read_parquet_as_view(file_path: str, view_name: str) -> str: return io_ops.read_parquet_as_view(file_path, view_name)

# ==========================================
# 5. Analysis
# ==========================================
@mcp.tool()
def get_column_stats(table_name: str, column_name: str) -> Dict[str, Any]: return analysis_ops.get_column_stats(table_name, column_name)
@mcp.tool()
def value_counts(table_name: str, column_name: str, limit: int = 20) -> List[Dict[str, Any]]: return analysis_ops.value_counts(table_name, column_name, limit)
@mcp.tool()
def correlation_matrix(table_name: str, col1: str, col2: str) -> float: return analysis_ops.correlation_matrix(table_name, col1, col2)
@mcp.tool()
def percentiles(table_name: str, column_name: str) -> Dict[str, float]: return analysis_ops.percentiles(table_name, column_name)
@mcp.tool()
def detect_outliers_zscore(table_name: str, column_name: str, threshold: float = 3.0) -> List[Dict[str, Any]]: return analysis_ops.detect_outliers_zscore(table_name, column_name, threshold)
@mcp.tool()
def summarize_table(table_name: str) -> str: return analysis_ops.summarize_table(table_name)
@mcp.tool()
def pivot_table(table_name: str, index_col: str, pivot_col: str, value_col: str, agg_func: str = "SUM") -> List[Dict[str, Any]]: return analysis_ops.pivot_table(table_name, index_col, pivot_col, value_col, agg_func)

# ==========================================
# 6. Super Tools
# ==========================================
@mcp.tool()
def etl_pipeline_csv(input_csv: str, output_parquet: str, filter_sql: str = "1=1") -> str: return super_ops.etl_pipeline_csv(input_csv, output_parquet, filter_sql)
@mcp.tool()
def merge_tables(table_a: str, table_b: str, join_col: str, output_table: str, join_type: str = "INNER") -> str: return super_ops.merge_tables(table_a, table_b, join_col, output_table, join_type)
@mcp.tool()
def query_remote_file(url: str, query_sql: str) -> str: return super_ops.query_remote_file(url, query_sql)
@mcp.tool()
def diff_tables(table_a: str, table_b: str, key_col: str) -> str: return super_ops.diff_tables(table_a, table_b, key_col)
@mcp.tool()
def sample_table(table_name: str, sample_size: int, output_table: str) -> str: return super_ops.sample_table(table_name, sample_size, output_table)
@mcp.tool()
def data_quality_report(table_name: str) -> str: return super_ops.data_quality_report(table_name)
@mcp.tool()
def convert_file_format(input_file: str, output_file: str) -> str: return super_ops.convert_file_format(input_file, output_file)
@mcp.tool()
def full_text_search(table_name: str, column_name: str, keyword: str) -> str: return super_ops.full_text_search(table_name, column_name, keyword)

# ==========================================
# 7. Spatial
# ==========================================
@mcp.tool()
def st_point(lat: float, lon: float) -> str: return spatial_ops.st_point(lat, lon)
@mcp.tool()
def st_distance(wkt_a: str, wkt_b: str) -> float: return spatial_ops.st_distance(wkt_a, wkt_b)
@mcp.tool()
def st_area(wkt_poly: str) -> float: return spatial_ops.st_area(wkt_poly)
@mcp.tool()
def st_contains(wkt_a: str, wkt_b: str) -> bool: return spatial_ops.st_contains(wkt_a, wkt_b)
@mcp.tool()
def st_intersects(wkt_a: str, wkt_b: str) -> bool: return spatial_ops.st_intersects(wkt_a, wkt_b)
@mcp.tool()
def st_buffer(wkt_geom: str, dist: float) -> str: return spatial_ops.st_buffer(wkt_geom, dist)
@mcp.tool()
def st_centroid(wkt_geom: str) -> str: return spatial_ops.st_centroid(wkt_geom)
@mcp.tool()
def st_read(file_path: str, table_name: str) -> str: return spatial_ops.st_read(file_path, table_name)
@mcp.tool()
def st_as_text(wkb_col: str, table_name: str) -> List[str]: return spatial_ops.st_as_text(wkb_col, table_name)
@mcp.tool()
def st_as_geojson(wkt_geom: str) -> str: return spatial_ops.st_as_geojson(wkt_geom)

# ==========================================
# 8. Text & JSON
# ==========================================
@mcp.tool()
def fts_create_index(table_name: str, id_col: str, text_cols: List[str]) -> str: return text_ops.fts_create_index(table_name, id_col, text_cols)
@mcp.tool()
def fts_search(table_name: str, keyword: str, limit: int = 20) -> List[Dict[str, Any]]: return text_ops.fts_search(table_name, keyword, limit)
@mcp.tool()
def json_extract_path(table_name: str, json_col: str, path: str) -> List[Any]: return text_ops.json_extract_path(table_name, json_col, path)
@mcp.tool()
def json_create(keys: List[str], values: List[Any]) -> str: return text_ops.json_create(keys, values)
@mcp.tool()
def regexp_extract(text: str, pattern: str) -> str: return text_ops.regexp_extract(text, pattern)
@mcp.tool()
def regexp_matches(text: str, pattern: str) -> bool: return text_ops.regexp_matches(text, pattern)
@mcp.tool()
def read_json_objects(file_path: str) -> List[Dict[str, Any]]: return text_ops.read_json_objects(file_path)

# ==========================================
# 9. Time Series
# ==========================================
@mcp.tool()
def time_bucket(table_name: str, time_col: str, interval: str, agg_col: str = "count(*)") -> List[Dict[str, Any]]: return time_ops.time_bucket(table_name, time_col, interval, agg_col)
@mcp.tool()
def gap_fill(table_name: str, time_col: str, interval: str, value_col: str) -> str: return time_ops.gap_fill(table_name, time_col, interval, value_col)
@mcp.tool()
def asof_join(table_a: str, table_b: str, time_col: str, join_col: str) -> str: return time_ops.asof_join(table_a, table_b, time_col, join_col)
@mcp.tool()
def lead_lag(table_name: str, col: str, order_col: str) -> List[Dict[str, Any]]: return time_ops.lead_lag(table_name, col, order_col)
@mcp.tool()
def moving_average(table_name: str, value_col: str, order_col: str, window: int) -> List[Dict[str, Any]]: return time_ops.moving_average(table_name, value_col, order_col, window)
@mcp.tool()
def date_diff(unit: str, start: str, end: str) -> int: return time_ops.date_diff(unit, start, end)
@mcp.tool()
def date_trunc(part: str, date: str) -> str: return time_ops.date_trunc(part, date)
@mcp.tool()
def make_timestamp(year: int, month: int, day: int, hour: int, min: int, sec: float) -> str: return time_ops.make_timestamp(year, month, day, hour, min, sec)

# ==========================================
# 10. Infra
# ==========================================
@mcp.tool()
def parquet_metadata(file_path: str) -> str: return infra_ops.parquet_metadata(file_path)
@mcp.tool()
def parquet_schema(file_path: str) -> str: return infra_ops.parquet_schema(file_path)
@mcp.tool()
def current_db_size() -> str: return infra_ops.current_db_size()
@mcp.tool()
def show_tables_expanded() -> str: return infra_ops.show_tables_expanded()
@mcp.tool()
def describe_table_detailed(table_name: str) -> str: return infra_ops.describe_table_detailed(table_name)
@mcp.tool()
def get_memory_usage() -> str: return infra_ops.get_memory_usage()
@mcp.tool()
def list_settings() -> str: return infra_ops.list_settings()
@mcp.tool()
def checkpoint_db() -> str: return infra_ops.checkpoint_db()
@mcp.tool()
def vacuum_db() -> str: return infra_ops.vacuum_db()
@mcp.tool()
def get_query_profiling(query: str) -> str: return infra_ops.get_query_profiling(query)

if __name__ == "__main__":
    mcp.run()
