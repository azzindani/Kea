# 🐍 Python Server (MCP)

The **Python Server** is a computational workbench for Project. it provides a secure, sandboxed environment for executing arbitrary Python code, performing complex data manipulations with Pandas, and running high-performance SQL queries over in-memory datasets using DuckDB.

## 🛠️ Tools

| Tool | Description |
|:-----|:------------|
| `execute_code` | Runs Python code in a isolated sandbox. Supports dynamic dependency installation via `uv` or `pip`. |
| `dataframe_ops` | Specialized wrapper for Pandas operations (load, transform, aggregate, join) without writing raw code. |
| `sql_query` | Executes analytical SQL queries using **DuckDB**. Can query CSV, JSON, and Parquet data sources directly. |

## 🏗️ Implementation

The server is built with a "Privacy First" approach:
- **Sandbox**: Execution is isolated to prevent host system interference (utilizes `uv run` for ephemeral environments).
- **DuckDB**: Provides a lightning-fast OLAP engine for relational analysis of research data.
- **Pandas**: The primary engine for the `dataframe_ops` tool, ensuring standard data science workflows are supported.

## 📦 Dynamic Dependencies

The `execute_code` tool allows specifying a `dependencies` list. The server automatically ensures these are available in the sandbox before execution, enabling the use of any library from the Python ecosystem (e.g., `scikit-learn`, `networkx`).
