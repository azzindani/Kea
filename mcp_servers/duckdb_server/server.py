
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

from shared.mcp.fastmcp import FastMCP
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
from shared.logging.main import setup_logging
setup_logging(force_stderr=True)

mcp = FastMCP("duckdb_server", dependencies=["pandas", "duckdb", "pyarrow"])

# ==========================================
# 1. Core
# ==========================================
# ==========================================
# 1. Core
# ==========================================
@mcp.tool()
def connect_db(path: str = "project_data.duckdb") -> str: 
    """CONNECTS to database. [ACTION]
    
    [RAG Context]
    The foundational "Super Tool" for high-performance analytical storage. It initializes or connects to a DuckDB database instance, which is optimized for fast OLAP (On-line Analytical Processing) queries on large datasets.
    
    How to Use:
    - Use ':memory:' for transient, lightning-fast scratchpad analysis.
    - Use a filename (e.g., 'vault_data.duckdb') for persistent storage that survives session restarts.
    - Enables SQL-based manipulation of data fetched from other MCP tools.
    
    Keywords: analytical database, sql engine, olap storage, data warehouse.
    """
    return core_ops.connect_db(path)

@mcp.tool()
def get_version() -> str: 
    """FETCHES the precise version of the underlying DuckDB engine. [ACTION]
    
    [RAG Context]
    A critical "Infrastructure Audit Tool" for ensuring compatibility and feature availability. DuckDB has been evolving rapidly, and some advanced SQL features—like specific window functions, nested types, or optimized parquet readers—are only available in newer versions. By checking the version, the Kea kernel can determine if the current environment supports the complex analytical queries it needs to run, or if it needs to fall back to a more conservative SQL dialect. It is a mandatory first step for any automated system that manages persistent data across different deployments.
    
    How to Use:
    - Simply call to get the version string (e.g., '1.1.0').
    - Essential for logging environment state during a "System Health Check" or before performing a database migration.
    
    Keywords: duckdb version, engine info, system compatibility, software audit, database versioning.
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
    """INSTALLS a specialized DuckDB extension to enable new SQL capabilities. [ACTION]
    
    [RAG Context]
    A vital "Feature Expansion Super Tool" for extending the database beyond standard SQL. DuckDB uses a modular architecture where massive libraries—like 'httpfs' (for reading data directly from URLs and S3), 'spatial' (for geographic GIS analysis), and 'icu' (for complex international timezones)—are downloaded only when needed. This keeps the core engine lean and fast. This tool allows the system to dynamically "Upgrade" its intelligence by pulling in the specific tools required for a task (e.g., install 'json' before parsing web logs).
    
    How to Use:
    - 'name': The name of the extension (e.g., 'httpfs', 'spatial', 'sqlite_scanner').
    - MUST be followed by 'load_extension' before the new SQL functions become active in the current session.
    - Essential for "Just-In-Time" infrastructure preparation.
    
    Keywords: install extension, plugin downloader, spatial toolkit, s3 support, database upgrade, dynamic feature loading.
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
    """SETS low-level configuration options to optimize database performance. [ACTION]
    
    [RAG Context]
    An elite "Performance Tuning Super Tool" for controlling the database engine's resources. Analysing massive datasets (Terabyte-scale) requires precise control over how the CPU and RAM are used. This tool allows the system to set limits on 'memory_limit' (to prevent crashing the host), 'threads' (to maximize multi-core parallel processing), and 'temp_directory' (for spill-to-disk analysis when RAM is full). It is a mandatory requirement for scaling the Kea system from a small laptop to a massive cloud-compute cluster without changing the underlying SQL logic.
    
    How to Use:
    - 'key': The name of the setting (e.g., 'memory_limit', 'access_mode', 'default_order').
    - 'value': The target setting value (e.g., '4GB', '8', 'READ_ONLY').
    - Critical for building "Safe" data pipelines that respect system hardware constraints.
    
    Keywords: database config, performance tuning, resource limit, thread count, memory management, low-level optimization.
    """
    return core_ops.set_config(key, value)

# ==========================================
# 2. Query
# ==========================================
@mcp.tool()
def execute_query(query: str) -> str: 
    """EXECUTES SQL query. [ACTION]
    
    [RAG Context]
    The primary tool for interacting with the database using standard SQL.
    
    How to Use:
    - Supports SELECT, INSERT, UPDATE, DELETE, and DDL statements.
    - Result is returned as a formatted ASCII table string for easy reading.
    - Use this for quick checks and debugging.
    
    Keywords: sql executor, run command, database query, raw sql.
    """
    return query_ops.execute_query(query)

@mcp.tool()
def fetch_all(query: str) -> List[Dict[str, Any]]: 
    """FETCHES all rows. [ACTION]
    
    [RAG Context]
    Executes a SELECT query and returns the entire result set as a machine-readable list of dictionaries.
    
    How to Use:
    - Best for tools that need to process data programmatically after retrieval.
    - Be careful with very large datasets; use LIMIT to prevent memory overflow.
    
    Keywords: data retrieval, json results, row fetch, set download.
    """
    return query_ops.fetch_all(query)

@mcp.tool()
def fetch_one(query: str) -> Dict[str, Any]: 
    """EXECUTES SQL and retrieves exactly one row as a structured dictionary. [ACTION]
    
    [RAG Context]
    A specialized "Lookup Super Tool" for point queries and aggregate status checks. While 'fetch_all' is for datasets, 'fetch_one' is the preferred way to retrieve single configuration records, current system status, or the result of a summary calculation (like `SELECT count(*) FROM table`). It is faster and more memory-efficient when the user only needs a single answer, as it informs the engine to stop processing as soon as the first matching record is found. Essential for state-checks and individual record inspection in automated workflows.
    
    How to Use:
    - Pass any valid SELECT query.
    - If the query returns multiple rows, only the first one is returned as a JSON-like dictionary.
    - Perfect for "Existence Checks" and finding the "latest" record in a sorted time-series.
    
    Keywords: single row fetch, point lookup, status check, quick query, record retrieval, aggregate result.
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
    """QUICKLY retrieves the total number of records in a specific table. [ACTION]
    
    [RAG Context]
    A fundamental "Data Velocity Super Tool" for auditing and telemetry. Before starting a long-running analysis, the system needs to know if it's dealing with 10 rows or 10 billion rows. This tool provides an instant "Pulse Check" on the size of the dataset. In the Kea corporate kernel, this count is used to dynamically scale hardware resources—if the count is high, the system will automatically allocate more threads and increase memory limits via 'set_config' before proceeding with complex joins or ML model training.
    
    How to Use:
    - 'table_name': The name of any existing table or view.
    - An essential step for "Data Quality Monitoring"—unexpected drops in row counts can trigger automated alerts about data ingestion failures.
    
    Keywords: row count, table size, record auditing, data volume, heartbeat check, table statistics.
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
    """RETRIEVES a complete inventory of all permanent tables in the current database. [ACTION]
    
    [RAG Context]
    A vital "Knowledge Discovery Tool" for exploring the database structure. In a RAG-enabled environment, the system often needs to know which "Data Silos" (Tables) are available before it can answer a user's question. This tool allows the reasoning kernel to map out the available entities, helping it decide whether it needs to query 'EmployeeRecords', 'FinancialData', or 'SensorLogs'. It provides the high-level "Table of Contents" for the analytical workspace, ensuring the AI never tries to query a table that doesn't exist.
    
    How to Use:
    - Simply call to get a list of all table names.
    - Often used in conjunction with 'get_table_schema' to understand the internal structure of a newly discovered data source.
    
    Keywords: list tables, database inventory, data discovery, schema exploration, table registry.
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
    """RETRIEVES a sample of data from a table to inspect its content and format. [ACTION]
    
    [RAG Context]
    An essential "Data Inspection Super Tool" for validating data quality and understanding data distributions. Before performing heavy-duty machine learning or complex joins, the kernel needs to "See" the data to ensure the formatting (dates, currency, categories) matches its expectations. This tool provides a non-destructive way to peek into massive datasets without loading millions of rows into memory, allowing for rapid hypothesis testing and debugging of data ingestion pipelines.
    
    How to Use:
    - 'table_name': The target table to inspect.
    - 'limit': The maximum number of rows to return (default 100,000). Useful for getting enough data for a "Mini-Analysis" while keeping latency low.
    - Returns a list of dictionaries, perfect for immediate processing or human-readable reporting.
    
    Keywords: data preview, table inspection, row sampling, content audit, data sanity check.
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
    """ESTABLISHES a new permanent storage table with a specific columnar schema. [ACTION]
    
    [RAG Context]
    A foundational "Data Definition Super Tool" for building the vault's structure. DuckDB is a strongly-typed database, meaning you must define whether a column is an INTEGER, VARCHAR, or TIMESTAMP before you can save data into it. This tool allows the system to build "Custom Silos" for new datasets it discovers—for example, creating a 'SocialMediaSentiment' table after a web scraping task. It ensures that data is stored in a structured, queryable, and high-performance format that survives beyond the current reasoning cycle.
    
    How to Use:
    - 'columns': A dictionary where keys are column names (e.g., 'user_id') and values are SQL types (e.g., 'BIGINT', 'DOUBLE', 'DATE').
    - Essential for organizing long-term corporate knowledge and ensuring data integrity across different agent tasks.
    
    Keywords: create table, database schema design, data definition, structured storage, table provisioning.
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
    """CREATES a Virtual Table (View) based on a saved SQL query. [ACTION]
    
    [RAG Context]
    An elite "Semantic Mapping Super Tool" for simplifying complex data relationships. A View doesn't store data itself; it stores a "Rule" for looking at data. This allows the system to create a "Clean Version" of a messy database—for example, creating a view called 'SuccessfulSales' that only shows records where `status = 'COMPLETED'`. Views are essential for providing the LLM and subsequent agents with a simplified, "Pre-Processed" lens on the raw data, making reasoning faster and reducing the complexity of future SQL queries.
    
    How to Use:
    - 'query': A standard SELECT statement that defines the view.
    - Use views to build "Data Dashboards" that hide the complexity of complex joins from the end user or decision-making kernel.
    - Views auto-update: if the underlying table data changes, the view always shows the latest state.
    
    Keywords: sql view, virtual table, query abstraction, data cleaning, semantic layer, saved query.
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
    """RAPIDLY ingests data from a CSV file into a high-performance database table. [ACTION]
    
    [RAG Context]
    The primary "Gateway Super Tool" for bringing external flat-file data into the analytical environment. CSV is the universal language of business data, but it is slow and hard to query. By importing it into DuckDB, the system "Upgrades" the file into a high-speed columnar database format. This tool is capable of reading millions of rows per second, with automatic schema detection that identifies dates, numbers, and categories without human intervention. It is the mandatory first step for processing spreadsheets, logs, and legacy exports within the Kea system.
    
    How to Use:
    - 'file_path': The location of the CSV file.
    - 'auto_detect': When true (default), the system "guesses" the structure perfectly.
    - 'table_name': The name of the target table (will be created if it doesn't exist).
    
    Keywords: csv import, bulk data load, flat file ingest, delimited data, spreadsheet migration, high-speed ingestion.
    """
    return io_ops.import_csv(file_path, table_name, auto_detect)

@mcp.tool()
def import_parquet(file_path: str, table_name: str) -> str: 
    """DIRECTLY loads or links a Parquet file into the database with zero-copy efficiency. [ACTION]
    
    [RAG Context]
    An elite "Modern Data Super Tool" for interacting with Big Data and Cloud storage. Parquet is the industry standard for "Columnar Storage," used by Data Lake systems like Spark and Snowflake. Unlike CSV, Parquet already knows its schema and is heavily compressed. This tool allows DuckDB to read these professional-grade files instantly—often faster than reading from local memory. It is the primary method for the Kea system to interact with "External Intelligence" and "Deep History" stored in corporate data lakes or S3 buckets.
    
    How to Use:
    - 'file_path': Can be a local path or a remote URL (if the 'httpfs' extension is loaded).
    - Perfect for "Zero-ETL" workflows where the system needs to analyze massive logs without a slow import process.
    
    Keywords: parquet import, columnar data, big data link, data lake ingest, apache arrow, compressed storage.
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
    """SAVES the results of a table or complex query into a universal CSV file. [ACTION]
    
    [RAG Context]
    A vital "Data Delivery Super Tool" for communicating findings with external systems or human operators. While the database is great for processing, CSV is what people expect in an email or a report. This tool allows the AI to "Package" its analytical results—like a list of 'Anomalous Transactions' or a 'Monthly Sales Summary'—into a file that can be opened in Excel or uploaded to another platform. It is the primary tool for "Closing the Loop" on a data analysis task by producing a tangible, portable artifact.
    
    How to Use:
    - 'table_or_query': Can be a simple table name or a full SELECT statement (e.g., `SELECT * FROM sales WHERE total > 1000`).
    - 'file_path': The destination on the filesystem.
    - Essential for generating downloadable datasets and report enclosures.
    
    Keywords: csv export, data packaging, report generation, artifact output, file export, spreadsheet share.
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
    """GENERATES a comprehensive statistical profile of an entire database table. [ACTION]
    
    [RAG Context]
    The absolute "Exploratory Data Analysis (EDA) Super Tool" for the Kea analytical stack. Before any reasoning can begin, the AI must understand the "Shape" of the data it is working with. This tool automatically calculates the count of records, average values (mean), spread (standard deviation), range (min/max), and the number of unique entries for every column in the table. It allows the system to instantly detect if a column is mostly empty, contains outliers, or holds categorical data that needs encoding. It is a mandatory first step for any automated data-science or financial-auditing task.
    
    How to Use:
    - 'table_name': The target table or view to analyze.
    - Yields a structured report that informs the kernel whether it should proceed with heavy modeling or if the data needs "Healing" (Imputation/Cleaning) first.
    
    Keywords: table summary, data profiling, automated eda, statistics overview, data quality audit, columnar analysis.
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
    """EXECUTES a high-speed Extract-Transform-Load (ETL) operation from CSV to Parquet. [ACTION]
    
    [RAG Context]
    A heavy-duty "Data Engineering Super Tool" designed for industrial-scale data preparation. Most real-world data starts as messy CSV files, which are inefficient for high-speed analysis. This tool automates the three core stages of data engineering: (1) Extracting raw text data from the source, (2) Transforming it using the provided SQL filter (e.g., removing negative prices or old records), and (3) Loading it into the professional-grade Parquet format. This results in a 10x to 100x speed increase for all subsequent queries. It is the primary engine for "Data Lake Modernization" within the corporate kernel.
    
    How to Use:
    - 'input_csv': The source file path.
    - 'output_parquet': The destination path for the optimized file.
    - 'filter_sql': A SQL WHERE clause (e.g., `revenue > 0`) to prune data during transfer.
    
    Keywords: etl pipeline, data transformation, csv conversion, parquet encoding, batch processing, data engineering.
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
    A high-level "Super Tool" that allows running SQL directly against files hosted on the web (S3, HTTP, HTTPS) without downloading them manually first.
    
    How to Use:
    - Supports remote Parquet, CSV, and JSON files.
    - DuckDB uses HTTP range requests to only download necessary chunks of data (Zero-Copy).
    
    Keywords: remote sql, s3 query, cloud data access, zero copy.
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
    """CREATES a standardized GIS geometry point from latitude and longitude coordinates. [ACTION]
    
    [RAG Context]
    The foundational "Spatial Mapping Super Tool" for location-based analysis. In a corporate environment, this is used to convert raw address coordinates into "Geospatial Objects" that can be mathematically compared. Unlike simple strings, these points allow the system to calculate physical distances, check if a delivery is within a specific "Geofence," or identify the nearest retail branch to a customer. This tool bridges the gap between raw numerical data and physical geographical reality, enabling the AI to reason about the "Where" of its operations.
    
    How to Use:
    - 'lat' & 'lon': Standard GPS decimal coordinates.
    - Resulting WKT (Well-Known Text) string can be saved into a 'GEOMETRY' column for high-speed spatial indexing and distance calculations.
    - Essential for logistics optimization, real-estate analysis, and supply-chain mapping.
    
    Keywords: spatial point, coordinate conversion, gis geometry, wkt creation, latitude longitude, geo-mapping.
    """
    return spatial_ops.st_point(lat, lon)

@mcp.tool()
def st_distance(wkt_a: str, wkt_b: str) -> float: 
    """CALCULATES the precise geographical distance between two spatial objects. [ACTION]
    
    [RAG Context]
    A critical "Logistics & Proximity Super Tool." This tool goes beyond simple math by calculating the distance between complex shapes or points on the Earth's surface. It allows the system to answer questions like: "How far is this warehouse from the shipping port?" or "Which branch is closest to the identified anomaly?" In the Kea corporate system, this is the primary engine for shipping-cost optimization and territorial assignments, ensuring that resources are always allocated to the most geographically efficient location.
    
    How to Use:
    - 'wkt_a' & 'wkt_b': Standard spatial strings (Points, Polygons, etc.).
    - Returns a numerical value (usually in meters or degrees depending on the coordinate system).
    - Can be used in SQL WHERE clauses to find items "within X distance" of a target coordinate.
    
    Keywords: spatial distance, proximity analysis, geo-distance, gis calculation, logistics math, location audit.
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
    """INGESTS complex geospatial files (Shapefiles, GeoJSON) into the database. [ACTION]
    
    [RAG Context]
    A professional-grade "GIS Ingestion Super Tool." While CSVs are row-based, GIS files (like ESRI Shapefiles or KML) contain complex multi-dimensional data like city boundaries, power grids, or property lines. This tool allows the Kea system to "Digest" official geographical records from government or industry sources and merge them with internal corporate data. It enables the system to perform high-stakes analysis, such as: "Is our proposed site located within a high-risk flood zone or protected forest area?"
    
    How to Use:
    - 'file_path': The path to a .shp, .json, or .kml file.
    - Requires the 'spatial' extension to be installed and loaded.
    - Translates specialized geographical formats into standard, queryable database tables with geometry support.
    
    Keywords: gis import, shapefile loader, geojson ingest, spatial data lake, cartographic analysis, map data load.
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
    """PERFORMS specialized Full-Text Search (FTS) to find keywords within large text datasets. [ACTION]
    
    [RAG Context]
    A powerful "Semantic Retrieval Super Tool" that enables the system to "Read" through millions of documents or log entries in milliseconds. While standard SQL uses 'LIKE' (which is slow), FTS uses a pre-built "Inverted Index" specifically optimized for natural language. It allows the system to find specific terms, phrases, or concepts across multiple columns simultaneously. This is the primary engine for "Regulatory Auditing" (searching for specific clauses in legal documents) and "Customer Support Mining" (finding all tickets related to a specific product bug).
    
    How to Use:
    - 'table_name': The table containing the text index.
    - 'keyword': The term or phrase you are looking for.
    - 'limit': Controls how many matches to return.
    - REQUIRES a prior call to 'fts_create_index' on the target columns.
    
    Keywords: full text search, keyword retrieval, semantic search, document mining, indexed search, text analytics.
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
    """AGGREGATES time-series data into standardized "Buckets" (e.g., hourly, daily). [ACTION]
    
    [RAG Context]
    An elite "Time-Series Intelligence Super Tool" for analyzing trends over time. High-frequency data (like stock prices or sensor readings) is often too noisy to understand in its raw form. Time Bucketing allows the system to "Zoom Out" and see the daily average or hourly count of events. It is a mandatory requirement for "Trend Analysis" and "Financial Forecasting," allowing the AI to transform a chaotic stream of individual timestamps into a structured report that shows growth, seasonal patterns, and cycles.
    
    How to Use:
    - 'time_col': The column containing timestamps or dates.
    - 'interval': The size of the bucket (e.g., '1 hour', '1 day', '7 days').
    - 'agg_col': The math to perform inside the bucket (e.g., `avg(price)`, `sum(volume)`, `count(*)`).
    
    Keywords: time bucket, temporal aggregation, trend analysis, time-series grouping, historical rollup, period analytics.
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
    """PERFORMS a sophisticated "ASOF Join" to align datasets with different timestamps. [ACTION]
    
    [RAG Context]
    A specialized "Temporal Alignment Super Tool" essential for finance and IoT analysis. In many cases, you have two data streams (e.g., 'Target Stock Price' and 'Macro-Economic Indicator') that don't share the exact same second-by-second timestamps. A standard join would fail. An ASOF join finds the record in Table B that was the "Most Recent" at the time of the record in Table A. It allows the system to answer: "What was the interest rate at the exact moment this specific trade was executed?" Mandatory for high-precision backtesting and causal analysis.
    
    How to Use:
    - 'table_a' & 'table_b': The two datasets to merge.
    - 'time_col': The timestamp column used for the temporal matching.
    - 'join_col': The attribute column (e.g., 'ticker_symbol') to ensure you are matching the right entities.
    
    Keywords: asof join, temporal alignment, time-series merge, financial data join, proximity join, nearest-neighbor time.
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

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class DuckdbServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []

