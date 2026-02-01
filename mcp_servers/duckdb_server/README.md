# 🦆 DuckDB Server ("The IT Department")

The **DuckDB Server** is the **IT and Data Engineering Department** of the Kea v4.0 system. It provides a high-performance, in-process SQL OLAP engine capable of crunching millions of rows in milliseconds. It serves as the local "Data Warehouse" for the Orchestrator, allowing agents to perform complex joins, aggregations, and transformations on data fetched from other sources.

## ✨ Features

- **In-Process Speed**: No network overhead. Executes SQL directly on dataframes and Parquet files.
- **Universal Format Support**: Reads and writes CSV, JSON, Parquet, and Excel natively.
- **Spatial Analytics**: Built-in support for Geospatial operations (`st_distance`, `st_contains`).
- **Time-Series Engine**: Specialized functions for `asof_join`, `time_bucket`, and gap filling.
- **ETL Super-Tools**: Can run full "Extract-Transform-Load" pipelines in a single tool call (`etl_pipeline_csv`).
- **Vectorized Execution**: Uses SIMD instructions to process columnar data efficiently.

## 🏗️ Architecture

The server exposes a massive library of 50+ tools, organized by function.

```mermaid
graph TD
    Agent[Agent] -->|SQL/ETL| API[DuckDB Server]
    
    API --> Query[Query Engine]
    API --> IO[Import/Export]
    API --> Spatial[GeoSpatial]
    API --> Time[Time Series]
    API --> Schema[Schema Ops]
    
    IO -->|Read/Write| Bus[Artifact Bus (Parquet)]
    Query -->|Analyze| Memory[In-Memory Tables]
```

## 🔌 Tool Categories

### 1. Core & Query
- `execute_query`: Run raw SQL (Power User tool).
- `preview_table`: Smart sampling of large datasets.
- `explain_query`: Query plan analysis for performance tuning.

### 2. Import/Export (The Bridge)
- `import_csv` / `import_parquet`: Load artifacts from the Vault into SQL tables.
- `export_parquet`: Dump query results back to the Vault for other agents.
- `read_parquet_as_view`: Zero-copy querying of large files.

### 3. Analysis & Statistics
- `correlation_matrix`: Calculate Pearson correlation.
- `detect_outliers_zscore`: Statistical anomaly detection.
- `pivot_table`: Excel-style pivoting via SQL.

### 4. Time Series
- `asof_join`: The "Holy Grail" of financial data merging (joining strictly inequality timestamps).
- `time_bucket`: Downsampling ticks to candles (1min, 1h, 1d).
- `moving_average`: Window functions.

### 5. Spatial
- `st_distance`: Calculate distance between coordinates.
- `st_point`: Geometry creation.
- `st_contains`: Geofencing checks.

### 6. Super Tools (ETL)
- `etl_pipeline_csv`: One-shot cleaning: `CSV -> Filter -> Parquet`.
- `merge_tables`: High-level join utility.
- `diff_tables`: Compare two tables row-by-row.

## 🚀 Usage

```python
# 1. Load Data
await client.call_tool("import_parquet", {
    "file_path": "/vault/prices.parquet", 
    "table_name": "prices"
})

# 2. Analyze (Compute Daily VWAP)
sql = "SELECT date_trunc('day', time), sum(price * volume) / sum(volume) as vwap FROM prices GROUP BY 1"
result = await client.call_tool("execute_query", {"query": sql})
```

## 🛠️ Configuration
- **Dependencies**: `duckdb`, `pandas`, `pyarrow`.
- **Performance**: Capable of processing 10GB+ datasets on a standard laptop.
