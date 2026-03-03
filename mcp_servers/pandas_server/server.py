
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)


from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
# from mcp_servers.pandas_server.tools import (
#     io_ops, inspection_ops, core_ops, transform_ops, chain_ops, 
#     time_ops, text_ops, stat_ops, struct_ops, ml_ops, logic_ops, 
#     window_ops, math_ops, quality_ops, nlp_ops, feature_ops
# )
# Note: Tools will be imported lazily inside each tool function to speed up startup.

import structlog
from typing import List, Union, Dict, Any, Optional

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging(force_stderr=True)


mcp = FastMCP("pandas_server", dependencies=["ydata-profiling", "pandas", "numpy", "structlog", "requests"])

# ==========================================
# 1. IO Operations
# ==========================================
@mcp.tool()
def read_dataset(file_path: str, format: str = None) -> dict:
    """READS dataset metadata and preview. [ENTRY]
    
    [RAG Context]
    This is the primary entry point for working with external data files. It acts as a universal reader capable of parsing CSV, Excel (XLSX), Parquet, and JSON formats into a structured Pandas DataFrame context.
    
    How to Use:
    - Provide the absolute 'file_path' to the local or networked file.
    - If 'format' is omitted, the tool will attempt to infer it from the file extension.
    - Returns a JSON dictionary containing the column names, detected data types (dtypes), total row count, and a preview of the first 5 rows (head).
    
    Arguments:
    - file_path (str): Path to the source file.
    - format (str): Optional override ('csv', 'excel', 'parquet', 'json').
    
    Keywords: load data, open file, csv reader, excel import, parquet preview, data ingestion.
    """
    from mcp_servers.pandas_server.tools import io_ops
    return io_ops.read_dataset(file_path, format=format)

@mcp.tool()
def convert_dataset(source_path: str, dest_path: str, source_format: str = None, dest_format: str = None) -> str:
    """CONVERTS dataset file format. [ACTION]
    
    [RAG Context]
    A vital "Super Tool" for data infrastructure optimization and format migration. Professional data environments often require a balance between human readability (CSV/Excel) and machine performance (Parquet/JSONL). This tool facilitates the seamless movement of data between these formats, enabling you to "compact" a massive, slow-loading CSV into a high-performance, compressed Parquet file for rapid analytical querying. Conversely, it can export technical data into formatted Excel spreadsheets for executive presentation or legacy business processes.
    
    How to Use:
    - 'source_path': Absolute path to the original file.
    - 'dest_path': The destination path where the new file will be created.
    - 'dest_format': Choose from 'csv', 'excel', 'parquet', or 'json'.
    - Use this tool at the end of a processing pipeline to save your final results in the format most suitable for the end-user or downstream system.
    
    Keywords: format conversion, csv to parquet, excel export, data migration, compression optimization, file transcode, save-as operation.
    """
    from mcp_servers.pandas_server.tools import io_ops
    return io_ops.convert_dataset(source_path, dest_path, source_format, dest_format)

@mcp.tool()
def get_dataset_info(file_path: str) -> dict:
    """GETS detailed dataset metadata and health metrics. [DATA]
    
    [RAG Context]
    An indispensable "Super Tool" for technical data auditing and resource management. In large-scale enterprise environments, loading a file blindly can lead to system crashes or memory exhaustion. This tool provides a deep-dive "health check" of the dataset without necessarily loading the entire content into active memory. It returns precise row counts, memory footprints, and critical data-hygiene metrics such as lists of missing values and column data types. It is the mandatory first step for any automated agent performing a feasibility assessment on a new data source.
    
    How to Use:
    - Provide the path to the dataset you wish to investigate.
    - Review the 'memory_usage' and 'row_count' to decide if the data should be sampled before further processing.
    - Check 'null_counts' to identify columns that might require aggressive cleaning or imputation using 'fill_na'.
    
    Keywords: file metadata, memory audit, row count, null detection, data health check, resource estimation, schema inspection.
    """
    from mcp_servers.pandas_server.tools import io_ops
    return io_ops.get_file_info(file_path)


# ==========================================
# 2. Inspection Operations
# ==========================================
@mcp.tool()
def head(file_path: str, n: int = 5) -> list:
    """GETS first n rows of dataset for rapid inspection. [DATA]
    
    [RAG Context]
    A foundational "Super Tool" for high-speed data validation and structural verification. When working with unfamiliar datasets, the 'head' tool provides an immediate, low-cost preview of the data's content, column alignment, and labeling style. By retrieving only the topmost records, it allows for "spot-checking" of data quality—such as verifying header correctness, identifying unexpected symbols, or confirming that numerical values match expected ranges—without the significant computational cost of processing the entire file.
    
    How to Use:
    - 'n': The number of leading rows to retrieve (default is 5).
    - Use this as your "first look" at any new data source to ensure the file was parsed correctly and meets your immediate analytical needs.
    - Essential for agents to confirm "Data Context" before generating complex transformation logic.
    
    Keywords: data preview, top records, row sampling, head inspection, initial glane, structural audit, data validation.
    """
    from mcp_servers.pandas_server.tools import inspection_ops
    return inspection_ops.inspect_head(file_path, n)

@mcp.tool()
def tail(file_path: str, n: int = 5) -> list:
    """GETS last n rows of dataset. [DATA]
    
    [RAG Context]
    A specialized "Super Tool" for auditing the chronological end or structural conclusion of a dataset. In many real-world exports, errors or trailing aggregate rows (totaling the columns) are common at the end of the file. This tool allows for the immediate inspection of the most recently added records or the final row-terminators, ensuring that no corruption or summary-row noise exists that could interfere with downstream mathematical calculations.
    
    How to Use:
    - 'n': The number of trailing rows to retrieve (default is 5).
    - Use this alongside 'head' to gain a complete understanding of the dataset's range and boundaries.
    - Perfect for verifying that a data-export process completed successfully without truncating the final records.
    
    Keywords: end-of-file audit, bottom records, trailing rows, range verification, tail inspection, closure check.
    """
    from mcp_servers.pandas_server.tools import inspection_ops
    return inspection_ops.inspect_tail(file_path, n)

@mcp.tool()
def columns(file_path: str) -> list:
    """GETS a comprehensive list of all column headers. [DATA]
    
    [RAG Context]
    A fundamental "Super Tool" for structural discovery and query preparation. Before any data manipulation can occur, the system must know exactly which keys/headers are available. This tool returns the complete schema of the dataset as a simple list of strings. It is the primary method for resolving "KeyError" issues, standardizing naming conventions, and preparing arguments for subsequent tools like 'select_columns', 'filter_data', or 'group_by'.
    
    How to Use:
    - Provide the file path to receive the full list of available features.
    - Use this to identify the exact spelling and casing of headers, as professional data tools are case-sensitive.
    - Essential for mapping fields when merging two disparate datasets from different corporate departments.
    
    Keywords: schema discovery, header list, field names, key identification, column mapping, dictionary of keys.
    """
    from mcp_servers.pandas_server.tools import inspection_ops
    return inspection_ops.inspect_columns(file_path)

@mcp.tool()
def dtypes(file_path: str) -> dict:
    """GETS column data types (Schema Typing). [DATA]
    
    [RAG Context]
    A technical "Super Tool" for data integrity and type-safety verification. In data science, performing math on strings or date-logic on raw text is impossible. This tool exposes the internal representation of every column in the dataset (e.g., Integer, Float, DateTime, Boolean, or Object). By inspecting these types early, you can identify "Type Casting" issues—such as a price column being incorrectly loaded as a string—and correct them using the 'astype' tool before they cause failures in downstream calculations or machine learning models.
    
    How to Use:
    - Returns a dictionary mapping each header to its detected Pandas dtype.
    - Focus on 'object' types; if they represent numbers or dates, they require explicit conversion for performance and calculation accuracy.
    - Fundamental for ensuring that the analytical engine is interpreting your data with the correct mathematical precision.
    
    Keywords: schema typing, data format check, type safety, field classification, technical schema, casting verification.
    """
    from mcp_servers.pandas_server.tools import inspection_ops
    return inspection_ops.inspect_dtypes(file_path)

@mcp.tool()
def describe(file_path: str) -> dict:
    """CALCULATES high-level descriptive statistics. [DATA]
    
    [RAG Context]
    A primary "Super Tool" for automated Exploratory Data Analysis (EDA). This tool generates a comprehensive overview of the distribution, central tendency, and dispersion of all numeric columns in the dataset. It provides a "statistical portrait" that includes the Mean, Standard Deviation, Minimum, Maximum, and the Interquartile Range (25%, 50%, 75%). It is the quickest way to identify if your data is "skewed," if it contains extreme outliers, or if the overall scale of the numbers is appropriate for the intended analysis.
    
    How to Use:
    - Run this on any dataset to immediately understand its mathematical "shape."
    - Compare the 'mean' and the '50%' (median) to detect bias; if they are significantly different, your data may be heavily skewed.
    - Use the 'std' (standard deviation) to judge the volatility or consistency of your metrics.
    
    Keywords: descriptive statistics, distribution summary, central tendency, dispersion metrics, data profiling, mathematical overview.
    """
    from mcp_servers.pandas_server.tools import inspection_ops
    return inspection_ops.inspect_describe(file_path)

@mcp.tool()
def value_counts(file_path: str, column: str, n: int = 10) -> dict:
    """COUNTS unique value frequencies (Categorical Analysis). [DATA]
    
    [RAG Context]
    A vital "Super Tool" for understanding the composition and diversity of categorical data. It scans a specific column and counts exactly how many times each unique value appears, presenting the results in descending order of frequency. This is the primary method for identifying "dominant" categories (e.g., "Which region has the most sales?") and "rare" categories (e.g., identifying low-occurrence error codes). It is essential for feature auditing, demographic segmentation, and identifying bias in classification datasets.
    
    How to Use:
    - 'column': The name of the categorical header to analyze.
    - 'n': The number of top unique values to retrieve (default is 10).
    - Use this to answer crucial business questions: "Who are our top 10 customers?" or "What are the most common reasons for support tickets?".
    
    Keywords: frequency distribution, category counts, unique value tally, demographic audit, value diversity, dominance analysis.
    """
    from mcp_servers.pandas_server.tools import inspection_ops
    return inspection_ops.inspect_value_counts(file_path, column, n)

@mcp.tool()
def shape(file_path: str) -> tuple:
    """GETS dataset dimensions (Structure Audit). [DATA]
    
    [RAG Context]
    A fast and lightweight "Super Tool" for measuring dataset scale. It returns a tuple containing the exact number of rows and columns in the file without the overhead of complex statistical processing. This "structural footprint" is a mandatory input for many data operations, such as ensuring that two files are compatible for horizontal concatenation or verifying that a filter operation successfully reduced the dataset to the expected size.
    
    How to Use:
    - Returns (rows, columns). 
    - Use this after any "reduction" operation (like 'filter_data' or 'drop_duplicates') to confirm exactly how many records were affected.
    - Crucial for informing an agent about the "volume" of work required before attempting memory-intensive tasks.
    
    Keywords: data dimensionality, size audit, record count, column width, structural footprint, matrix scale.
    """
    from mcp_servers.pandas_server.tools import inspection_ops
    return inspection_ops.inspect_shape(file_path)


# ==========================================
# 3. Core Operations
# ==========================================
@mcp.tool()
def filter_data(file_path: str, query: str, output_path: str) -> str:
    """FILTERS rows using SQL-like query. [ACTION]
    
    [RAG Context]
    The primary "Super Tool" for data selection and subsetting. It allows users to isolate specific records from a dataset using a highly efficient, string-based query engine. This tool processes the data row by row (using the underlying Pandas numexpr or python engines) to identify matches against complex boolean expressions. It is significantly more efficient than manually iterating over rows and is the industry standard for narrowing down large data collections into manageable, insight-focused slices.
    
    How to Use:
    - The 'query' argument takes a boolean expression string.
    - Examples: 
        - Numeric: `revenue > 5000000` (Finds high-performing entities).
        - Categorical: `status == "Pending" or priority == "Critical"` (Isolates urgent tasks).
        - Date-based: `order_date >= "2023-01-01"` (Limits analysis to recent fiscal periods).
        - Advanced: `city in ["New York", "London"] and age.between(25, 45)`.
    - Use this frequently as the first step in any analytical pipeline to reduce "noise" and focus only on relevant data points.
    
    Keywords: data filtering, subsetting, boolean indexing, record selection, search database, conditional logic.
    """
    from mcp_servers.pandas_server.tools import core_ops
    return core_ops.filter_data(file_path, query, output_path)

@mcp.tool()
def select_columns(file_path: str, columns: List[str], output_path: str) -> str:
    """KEEPS only specified columns. [ACTION]
    
    [RAG Context]
    An essential "Super Tool" for schema simplification and dimensionality reduction. This tool transforms a wide dataset (one with many columns) into a focused subset containing only the fields necessary for a specific analysis. By stripping away irrelevant data columns, it reduces the memory footprint of the data, accelerates subsequent processing steps (like sorting or aggregations), and makes the data much easier for both humans and AI agents to interpret. It is the "Select" part of a traditional ETL (Extract, Transform, Load) or SQL workflow.
    
    How to Use:
    - Provide a list of exact column names (headers) you wish to retain.
    - If you are unsure of the column names, run the 'columns' tool first to see the available schema features.
    - This is a destructive operation on the output file; only the specified columns will exist in the result. Always use this before sending data to expensive plotting or modeling tools to minimize data transfer overhead.
    
    Keywords: column selection, projection, field subset, vertical slice, schema reduction, data narrowing.
    """
    from mcp_servers.pandas_server.tools import core_ops
    return core_ops.select_columns(file_path, columns, output_path)

@mcp.tool()
def sort_data(file_path: str, by: Union[str, List[str]], ascending: bool, output_path: str) -> str:
    """SORTS dataset by column(s). [ACTION]
    
    [RAG Context]
    A fundamental "Super Tool" for data organization and prioritization. It reorders the entire dataset based on the quantitative or qualitative values within specified columns. Sorting is a prerequisite for many advanced operations, such as identifying the "top N" performers, analyzing time-series trends (which requires chronological order), or grouping similar items together. The tool supports multi-level sorting, allowing for complex hierarchies of organization (e.g., sorting by 'Region' alphabetically, and then by 'Annual Sales' in descending order).
    
    How to Use:
    - 'by': Pass a single column name or a list for hierarchical sorting.
    - 'ascending': Set to 'True' for ascending order (0 to 100, A to Z) or 'False' for descending order (100 to 0, Z to A).
    - Use this to prepare data for reporting (e.g., 'rank by profit') or to ensure that time-series data is processed correctly from the oldest to the newest entry.
    
    Keywords: data ordering, rank sorting, prioritization, list arrangement, alphabetical sort, chronological order.
    """
    from mcp_servers.pandas_server.tools import core_ops
    return core_ops.sort_data(file_path, by, ascending, output_path)

@mcp.tool()
def drop_duplicates(file_path: str, subset: Optional[List[str]] = None, output_path: str = "") -> str:
    """REMOVES duplicate rows. [ACTION]
    
    [RAG Context]
    A critical "Super Tool" for data hygiene and quality assurance. In real-world data collection, redundant records are common due to logging errors, merged sources, or double-entry. This tool scans the dataset to identify and discard rows that are identical. Removing duplicates is essential for accurate statistical analysis (e.g., ensuring a single purchase isn't counted twice) and for maintaining the integrity of unique identifiers in a database.
    
    How to Use:
    - By default, it checks for duplication across *all* columns (entire row must match).
    - 'subset': Specify a list of columns to define what makes a row "unique" (e.g., just 'customer_id' and 'transaction_date').
    - This is often the first step in a cleaning pipeline, immediately following data ingestion, to ensure the statistical "count" of your data is truthful.
    
    Keywords: data cleaning, uniqueness, de-duplication, record merging, clean data, redundancy removal.
    """
    from mcp_servers.pandas_server.tools import core_ops
    return core_ops.drop_duplicates(file_path, subset, output_path)

@mcp.tool()
def fill_na(file_path: str, value: Any, output_path: str, method: Optional[str] = None) -> str:
    """FILLS missing values (NaN). [ACTION]
    
    [RAG Context]
    A vital "Super Tool" for data imputation and completing sparse datasets. Missing data (NaN/Null) can break mathematical operations and cause errors in modern machine learning models. This tool provides multiple strategies for handling gaps in your records, allowing for either simple constant replacement or sophisticated algorithmic estimation based on surrounding data points. Properly addressing missing values is a cornerstone of professional data preprocessing.
    
    How to Use:
    - 'value': Use this to replace all NaNs with a specific scalar (e.g., 0 for counts, "Unknown" for categories).
    - 'method':
        - 'ffill' (forward-fill): Carries the last known valid observation forward until the next valid observation is found. This is best for time-series where data is semi-static.
        - 'bfill' (backward-fill): Uses the next valid observation to fill the gap behind it.
    - Choosing the right filling strategy prevents introducing statistical bias into your analysis.
    
    Keywords: data imputation, null handling, NaN replacement, missing values, data patching, completeness.
    """
    from mcp_servers.pandas_server.tools import core_ops
    return core_ops.fill_na(file_path, value, output_path, method)

@mcp.tool()
def sample_data(file_path: str, n: Optional[int] = None, frac: Optional[float] = None, output_path: str = "") -> str:
    """SAMPLES random rows. [ACTION]
    
    [RAG Context]
    A powerful "Super Tool" for handling massive datasets and performing rapid testing. When working with millions of rows, processing the entire file for every iteration can be prohibitively slow. This tool allows you to extract a representative random subset (a "sample") that preserves the overall characteristics of the population. Sampling is essential for developing models on "Big Data," creating training/testing splits, and performing feasibility checks on new analytical logic without consuming excessive system resources.
    
    How to Use:
    - 'n': Specify a fixed number of rows (e.g., set to 500 for a quick look).
    - 'frac': Specify a fraction of the total rows (e.g., 0.01 for 1% of the data).
    - Sampling is random, ensuring that you don't just see the first or last entries, which might be biased or sorted.
    
    Keywords: data sampling, random subset, data reduction, representative slice, big data testing, train test split.
    """
    from mcp_servers.pandas_server.tools import core_ops
    return core_ops.sample_data(file_path, n, frac, output_path)

@mcp.tool()
def astype(file_path: str, column_types: Dict[str, str], output_path: str) -> str:
    """CASTS column data types. [ACTION]
    
    [RAG Context]
    A technical "Super Tool" for ensuring type safety and correct mathematical processing. Frequently, data loaded from CSVs may contain numeric values interpreted as strings or dates interpreted as raw text. This tool explicitly converts columns into their intended formats (e.g., Integer, Float, DateTime, Boolean). Proper type casting is a prerequisite for any mathematical calculation (summing totals), date-based comparisons (calculating durations), or boolean filtering.
    
    How to Use:
    - 'column_types': A dictionary mapping column names to target types (e.g., `{"age": "int", "is_active": "bool", "salary": "float64"}`).
    - Using the correct type prevents "TypeError" bugs in later analysis and optimizes storage efficiency by using appropriate memory representations.
    
    Keywords: data type conversion, casting, type mapping, numeric parsing, date conversion, schema enforcement.
    """
    from mcp_servers.pandas_server.tools import core_ops
    return core_ops.astype(file_path, column_types, output_path)

@mcp.tool()
def rename_columns(file_path: str, mapping: Dict[str, str], output_path: str) -> str:
    """RENAMES columns. [ACTION]
    
    [RAG Context]
    An organizational "Super Tool" for data standardization and readability. This tool modifies the header labels of the dataset without altering the underlying data values. It is essential when merging datasets from different sources that use different naming conventions for the same data (e.g., renaming 'CustID' in one file and 'user_identifier' in another both to 'customer_id') or when preparing raw data for a final presentation or report.
    
    How to Use:
    - 'mapping': A dictionary where the keys are the current column names and the values are the new desired names (e.g., `{"old_name": "new_name"}`).
    - This tool makes code more maintainable by ensuring that all scripts in a pipeline refer to consistent, descriptive, and standardized headers.
    
    Keywords: column rebranding, alias, header update, schema renaming, label modification, data alignment.
    """
    from mcp_servers.pandas_server.tools import core_ops
    return core_ops.rename_columns(file_path, mapping, output_path)

@mcp.tool()
def set_index(file_path: str, columns: Union[str, List[str]], drop: bool = True, output_path: str = "") -> str:
    """SETS specified column as the dataset index. [ACTION]
    
    [RAG Context]
    A critical "Super Tool" for data structural alignment and performance optimization. In Pandas, the "index" is more than just a label; it is the organizational spine of the dataset. By promoting a column (like 'transaction_id', 'timestamp', or 'employee_code') to the index level, you enable higher-speed lookups and facilitate seamless alignment when performing arithmetic or joining with other datasets. This is a mandatory step for time-series analysis (where 'date' must be the index) and for creating sophisticated multi-dimensional (MultiIndex) hierarchies that organize data by nested categories (e.g., Region > Store > Department).
    
    How to Use:
    - 'columns': The name(s) of the header to promote to the index.
    - 'drop': If True (default), the source column is removed from the data body to prevent redundancy.
    - Essential for making complex data structures more navigable and for ensuring that the system can "lock onto" unique records with maximum efficiency.
    
    Keywords: indexing, structural alignment, primary key, row identifier, time-series prep, multi-index creation.
    """
    from mcp_servers.pandas_server.tools import core_ops
    return core_ops.set_index(file_path, columns, drop, output_path)

@mcp.tool()
def reset_index(file_path: str, drop: bool = False, output_path: str = "") -> str:
    """RESETS index to a sequential integer range. [ACTION]
    
    [RAG Context]
    A vital "Super Tool" for data normalization and record cleanup. After performing operations like 'filter_data', 'drop_duplicates', or 'group_by', the surviving rows often retain their original index numbers, leading to non-sequential or "holey" row labels (e.g., rows 1, 4, 15). This tool repairs the structural sequence by resetting the index to a clean, continuous progression from 0 to N. It is the "Refresh Button" for a dataset's structure, ensuring that all subsequent operations—such as selecting the "5th row"—yield predictable and accurate results based on the current state of the data rather than its historical state.
    
    How to Use:
    - Use this tool at the end of every transformation step to maintain a predictable, sequential structure.
    - 'drop': If True, the old index labels are discarded. If False, the old labels are preserved as a new regular column (useful for keeping track of original record IDs).
    
    Keywords: index normalization, sequential re-indexing, range update, record cleanup, structural reset, row number repair.
    """
    from mcp_servers.pandas_server.tools import core_ops
    return core_ops.reset_index(file_path, drop, output_path)


# ==========================================
# 4. Transformation Operations
# ==========================================
@mcp.tool()
def group_by(file_path: str, by: Union[str, List[str]], agg: Dict[str, Union[str, List[str]]], output_path: str) -> str:
    """GROUPS data and aggregates. [ACTION]
    
    [RAG Context]
    A powerful analytical "Super Tool" implementing the industry-standard Split-Apply-Combine pattern. This tool is the engine behind most descriptive reporting; it logically divides the dataset into groups based on unique values in specified columns (Split), applies mathematical operations like summing, averaging, or counting to each group (Apply), and compiles the results into a new structured summary table (Combine). It is essential for turning thousands of individual transactions into a handful of high-level insights, such as regional performance summaries or product category audits.
    
    How to Use:
    - 'by': The categorical field(s) you want to group by (e.g., 'country' or ['year', 'quarter']).
    - 'agg': A dictionary mapping your metric columns to the desired math operation (e.g., `{"revenue": "sum", "customer_id": "count"}`).
    - Common verbs include 'sum', 'mean', 'count', 'min', 'max', and 'std'.
    - Use this to answer executive-level questions: "Which department has the highest average salary?" or "What is our total inventory value per warehouse?".
    
    Keywords: data aggregation, summary statistics, group analysis, split apply combine, pivot summary, reporting engine.
    """
    from mcp_servers.pandas_server.tools import transform_ops
    return transform_ops.group_by(file_path, by, agg, output_path)

@mcp.tool()
def merge_datasets(left_path: str, right_path: str, on: Union[str, List[str]], how: str, output_path: str) -> str:
    """JOINS two datasets (SQL-style). [ACTION]
    
    [RAG Context]
    A foundational "Super Tool" for relational data modeling and information fusion. In professional data workflows, information is rarely stored in a single flat file; instead, it is distributed across multiple sources. This tool allows you to combine two separate datasets into a single, unified view based on a common key or "foreign key" (e.g., matching 'customer_id' in a Sales file with 'customer_id' in a Contact Info file). It replicates the full logic of SQL Join operations, enabling the creation of complex, multi-source records that are required for deep-dive business intelligence.
    
    How to Use:
    - 'on': The shared column name(s) used for the match.
    - 'how':
        - 'inner': Keep only the records where the key exists in *both* files (the intersection).
        - 'left': Keep all records from the first file, even if they have no match in the second.
        - 'outer': Keep all records from both files, filling gaps with NaNs (the union).
    - Crucial for enriching datasets with supplemental metadata from reference tables.
    
    Keywords: relational join, data merging, information fusion, sql join engine, lookup enrichment, linked data.
    """
    from mcp_servers.pandas_server.tools import transform_ops
    return transform_ops.merge_datasets(left_path, right_path, on, how, output_path)

@mcp.tool()
def concat_datasets(file_paths: List[str], axis: int, output_path: str) -> str:
    """COMBINES datasets vertically or horizontally. [ACTION]
    
    [RAG Context]
    A versatile "Super Tool" for dataset assembly and structural concatenation. Unlike a 'merge' which matches keys, 'concat' simply glues tables together along a chosen axis. This is the primary method for appending new data batches to a historical archive (vertical concatenation) or for attaching a large set of new calculated features to a base table (horizontal concatenation). It is essential for managing partitioned data, such as merging twelve individual monthly sales files into a single annual master record.
    
    How to Use:
    - 'axis=0' (Vertical): Use this to stack rows. Rows from the second file are placed below the rows of the first. Columns are aligned by name automatically.
    - 'axis=1' (Horizontal): Use this to side-stack columns. Files must have the same number of rows for the result to remain coherent.
    - Ideal for collecting data from multiple sensors, regions, or time periods into a unified processing pipeline.
    
    Keywords: batch appending, data stacking, row union, column binding, dataset assembly, vertical merge.
    """
    from mcp_servers.pandas_server.tools import transform_ops
    return transform_ops.concat_datasets(file_paths, axis, output_path)

@mcp.tool()
def pivot_table(file_path: str, values: str, index: Union[str, List[str]], columns: Union[str, List[str]], aggfunc: str, output_path: str) -> str:
    """RESHAPES data into a pivot table. [ACTION]
    
    [RAG Context]
    An advanced "Super Tool" for multi-dimensional data summarizing and reshaping. It replicates the sophisticated cross-tabulation functionality found in high-end spreadsheet software. This tool spreads unique categorical values from a single column across multiple new headers (pivoting), providing a wide-format view that is optimized for comparative analysis. It allows you to simultaneously analyze data across two different dimensions (e.g., comparing 'Sales Performance' by 'Month' on the rows and 'Product Category' on the columns).
    
    How to Use:
    - 'index': The column(s) that will form the rows of the new table.
    - 'columns': The column whose unique values will become the new headers.
    - 'values': The numerical field to be aggregated within the table cells.
    - 'aggfunc': The math operation to apply (e.g., 'sum', 'mean').
    - Essential for creating "Executive Dashboards" and comparative performance matrices.
    
    Keywords: crosstab summary, multi-dimensional analysis, spread data, wide-format report, comparative matrix.
    """
    from mcp_servers.pandas_server.tools import transform_ops
    return transform_ops.pivot_table(file_path, values, index, columns, aggfunc, output_path)

@mcp.tool()
def melt_data(file_path: str, id_vars: List[str], value_vars: Optional[List[str]], output_path: str) -> str:
    """UNPIVOTS wide data to long format. [ACTION]
    
    [RAG Context]
    A sophisticated "Super Tool" for data normalization and preparation. Many datasets are provided in a "Wide" format where multiple columns represent the same variable across different categories (e.g., columns for '2021_Sales', '2022_Sales'). This creates "untidy" data that is difficult to analyze with standard grouping or visualization tools. This tool "melts" those multiple columns into two new fields: a 'variable' column (containing the old header names) and a 'value' column (containing the actual data), effectively rotating the table to a "Long" format.
    
    How to Use:
    - 'id_vars': The columns you want to keep as unique identifiers for each row (e.g., 'product_id', 'store_location').
    - 'value_vars': The list of wide columns you want to collapse into rows. If omitted, all remainders are used.
    - Essential for making data "Tidy," which is a prerequisite for professional plotting libraries (Seaborn/Plotly) and modern database ingestion.
    
    Keywords: data unpivoting, normalization, tidy data, reshaping, long format, table rotation.
    """
    from mcp_servers.pandas_server.tools import transform_ops
    return transform_ops.melt_data(file_path, id_vars, value_vars, output_path)


# ==========================================
# 5. Time Series Operations
# ==========================================
@mcp.tool()
def to_datetime(file_path: str, columns: List[str], output_path: str, format: Optional[str] = None) -> str:
    """CONVERTS columns to datetime objects. [ACTION]
    
    [RAG Context]
    A foundational "Super Tool" for temporal data integrity. Raw data files often store dates as plain text or integers, which prevents the system from performing chronological arithmetic (like calculating the number of days between two events). This tool uses a sophisticated parser to transform those raw values into standardized Python/Pandas 'datetime64' objects. This transformation unlocks a suite of advanced temporal capabilities, including time-based sorting, resampling by frequency, and extracting seasonal components like 'day of the week' or 'fiscal quarter'.
    
    How to Use:
    - Provide the list of columns that represent dates.
    - If your dates are in a non-standard or ambiguous format (e.g., "01-02-03"), use the 'format' argument with standard strftime codes (e.g., "%d-%m-%y") to ensure unambiguous parsing.
    - Correct datetime casting is the most important step in preparing any financial or operational time-series for analysis.
    
    Keywords: date parsing, timestamp conversion, temporal types, datetime64, time normalization, calendar data.
    """
    from mcp_servers.pandas_server.tools import time_ops
    return time_ops.to_datetime(file_path, columns, output_path, format)

@mcp.tool()
def resample_data(file_path: str, rule: str, on: Optional[str] = None, agg: Dict[str, str] = None, output_path: str = "") -> str:
    """CHANGE time frequency (e.g. Daily -> Monthly). [ACTION]
    
    [RAG Context]
    A specialized "Super Tool" for time-series frequency conversion and data aggregation. In many scenarios, data is collected at a higher frequency than is needed for reporting (e.g., recording inventory levels every minute, but only needing daily summaries). This tool buckets those high-frequency timestamped records into custom time windows (e.g., Days, Weeks, Months) and applies a mathematical aggregate to each bucket. It is the primary method for "downsampling" large, noisy time-series into smooth, trend-focused datasets.
    
    How to Use:
    - 'rule': Use standard frequency codes like 'H' (Hourly), 'D' (Daily), 'W' (Weekly), 'M' (Month-End), or 'B' (Business Day).
    - 'agg': Define how to combine the data in each window (e.g., `{"temperature": "mean", "rainfall": "sum"}`).
    - This is essential for aligning datasets that were recorded at different intervals (e.g., merging daily stock prices with monthly inflation data).
    
    Keywords: time-series resampling, downsampling, frequency conversion, time bucketing, data aggregation, temporal smoothing.
    """
    from mcp_servers.pandas_server.tools import time_ops
    return time_ops.resample_data(file_path, rule, on=on, agg=agg, output_path=output_path)

@mcp.tool()
def rolling_window(file_path: str, window: int, agg: str, on: Optional[str] = None, columns: Optional[List[str]] = None, output_path: str = "") -> str:
    """CALCULATES moving averages/stats. [ACTION]
    
    [RAG Context]
    A technical "Super Tool" for signal smoothing and trend identification. When working with volatile data—such as day-to-day stock prices or hourly website traffic—short-term "noise" can often hide the underlying long-term direction. This tool computes a statistic (like the Mean or Standard Deviation) across a sliding window of previous observations. The resulting "Rolling Average" or "Moving Average" provides a much clearer picture of the data's trajectory and is a staple of technical financial analysis and scientific data processing.
    
    How to Use:
    - 'window': The number of consecutive rows to include in each calculation (e.g., a window of 7 on daily data creates a "7-day Moving Average").
    - 'agg': The type of calculation to perform (e.g., 'mean' for averages, 'std' for volatility/risk).
    - Use this to identify momentum in a market or to find periods of unusual variance in an industrial process.
    
    Keywords: moving average, SMA, sliding window, data smoothing, trend detection, volatility analysis, signal processing.
    """
    from mcp_servers.pandas_server.tools import time_ops
    return time_ops.rolling_window(file_path, window, agg, on, columns, output_path)

@mcp.tool()
def shift_diff(file_path: str, periods: int, columns: List[str], operation: str, output_path: str) -> str:
    """SHIFTS or DIFFS data for lags/changes. [ACTION]
    
    [RAG Context]
    A specialized "Super Tool" for analyzing sequential changes and momentum in numeric data. In time-series analysis, understanding the literal value of a record is often less important than understanding how it changed relative to the previous point in time. This tool enables two critical operations: 'Shift' (moving data points forward or backward in time to create "leads" or "lags") and 'Diff' (calculating the mathematical delta between current and previous periods). It is a fundamental component for building predictive models, identifying growth rates, and calculating rolling returns in finance.
    
    How to Use:
    - 'operation':
        - 'shift': Use `periods=1` to align today's row with yesterday's value (useful for calculating % change manually: `(today - yesterday) / yesterday`).
        - 'diff': Automatically calculates the difference (`Value[t] - Value[t-periods]`).
    - Essential for detecting "acceleration" or "deceleration" in metrics like revenue growth, website traffic, or sensor temperature changes.
    
    Keywords: lag analysis, lead data, rate of change, delta calculation, period comparison, momentum indicator.
    """
    from mcp_servers.pandas_server.tools import time_ops
    return time_ops.shift_diff(file_path, periods, columns, operation, output_path)

@mcp.tool()
def dt_component(file_path: str, column: str, component: str, output_path: str) -> str:
    """EXTRACTS date parts (year, month, day). [ACTION]
    
    [RAG Context]
    An indispensable "Super Tool" for temporal feature engineering. Raw dates often contain hidden patterns that are only visible when broken down into individual calendar components. This tool allows you to decompose a high-precision timestamp into its constituent parts—such as the Day of the Week, the Fiscal Quarter, or simply the Year. This decomposition is vital for identifying seasonal trends (e.g., "Do users spend more on Fridays?"), for performing year-over-year comparisons, and for creating categorical groups based on time intervals.
    
    How to Use:
    - 'component': Choose from a wide array of extractors including 'year', 'month', 'day', 'hour', 'dayofweek' (0=Monday, 6=Sunday), 'quarter', or boolean flags like 'is_month_start'.
    - Use this to transform a single 'order_date' column into multiple features that a machine learning model or reporting dashboard can use for segmentation.
    
    Keywords: temporal extraction, feature engineering, date decomposition, seasonality analysis, calendar attributes, time segmentation.
    """
    from mcp_servers.pandas_server.tools import time_ops
    return time_ops.dt_accessor(file_path, column, component, output_path)


# ==========================================
# 6. Text Operations
# ==========================================
@mcp.tool()
def str_split(file_path: str, column: str, pat: Optional[str] = None, expand: bool = True, output_path: str = "") -> str:
    """SPLITS string column by delimiter. [ACTION]
    
    [RAG Context]
    A versatile "Super Tool" for text parsing and structured data extraction. Data often arrives in "compact" string formats where multiple pieces of information are joined by a common separator (e.g., 'Lastname, Firstname' or 'Category-Subcategory'). This tool breaks those composite strings into their individual components based on a delimiter (pattern). By expanding these pieces into separate columns, you transform unstructured text into the machine-readable features required for professional database operations and statistical analysis.
    
    How to Use:
    - 'pat': The character or string used to define the split point (e.g., `-`, `_`, or even multi-character strings).
    - 'expand': When set to True (default), it creates a new dataset where each part of the split gets its own dedicated column (Column_0, Column_1, etc.).
    - Ideal for decomposing path strings, log entries, or concatenated identifiers into a clean, tabular format.
    
    Keywords: text tokenization, string decomposition, delimiter splitting, data parsing, column expansion, unstructured cleanup.
    """
    from mcp_servers.pandas_server.tools import text_ops
    return text_ops.str_split(file_path, column, pat, expand, output_path)

@mcp.tool()
def str_replace(file_path: str, column: str, pat: str, repl: str, regex: bool = False, output_path: str = "") -> str:
    """REPLACES pattern in string column. [ACTION]
    
    [RAG Context]
    A high-performance "Super Tool" for mass text correction and string sanitation. Real-world text data is often "dirty"—containing unwanted symbols, inconsistent naming, or legacy formatting that interferes with analysis. This tool scans a specific column and replaces all occurrences of a target pattern with a new value. It supports both simple literal replacement (e.g., replacing 'USA' with 'United States') and advanced Regular Expression (RegEx) matching for complex pattern-based cleaning (e.g., stripping all non-alphanumeric characters from a column).
    
    How to Use:
    - 'pat': The thing you want to find.
    - 'repl': The thing you want to put in its place.
    - 'regex': Set to True to unlock powerful pattern matching (e.g., using `[0-9]+` to target any digit sequence).
    - Crucial for data standardization, removing currency symbols, or correcting common clerical errors at scale.
    
    Keywords: text replacement, string substitution, regex cleanup, data sanitation, mass correction, pattern modification.
    """
    from mcp_servers.pandas_server.tools import text_ops
    return text_ops.str_replace(file_path, column, pat, repl, regex, output_path)

@mcp.tool()
def str_extract(file_path: str, column: str, pat: str, output_path: str = "") -> str:
    r"""EXTRACTS regex groups from text. [ACTION]
    
    [RAG Context]
    A precision "Super Tool" for information mining from unstructured text data. Many columns contain semi-structured patterns—such as item codes, email addresses, or specific product IDs—embedded within longer text strings. This tool uses Regular Expressions (RegEx) with capture groups `()` to pinpoint and pull these specific substrings into their own dedicated columns. It is the primary method for transforming raw, multi-part strings (e.g., a "Log" entry) into clear, structured features (e.g., just the "Error Code").
    
    How to Use:
    - 'pat': Use a RegEx string with parentheses to define what to pull (e.g., `pat="(@[\w\.]+)"` to extract the domain from an email).
    - If there are multiple capture groups, the tool creates multiple columns in the output.
    - Essential for sophisticated data extraction where simple splitting is not enough due to irregular delimiters or complex internal structures.
    
    Keywords: regex mining, pattern extraction, information retrieval, substring capture, structured text, data parsing.
    """
    from mcp_servers.pandas_server.tools import text_ops
    return text_ops.str_extract(file_path, column, pat, output_path)

@mcp.tool()
def str_case(file_path: str, column: str, case: str, output_path: str = "") -> str:
    """CONVERTS text case (lower/upper/title) for normalization. [ACTION]
    
    [RAG Context]
    A fundamental "Super Tool" for text standardization and qualitative data hygiene. In raw data exports, text fields often contain inconsistent capitalization (e.g., "Apple", "apple", and "APPLE" appearing in the same column), which causes analytical tools to treat them as different entities. This tool enforces a uniform casing strategy across the entire column simultaneously. It is a mandatory preprocessing step for any categorical analysis, text searching, or relational merging where case-sensitivity could lead to missed matches or fragmented reporting.
    
    How to Use:
    - 'case': 
        - 'lower': Ideal for joins and internal comparisons.
        - 'upper': Good for standardized codes or acronyms.
        - 'title': Perfect for preparing human-readable reports with names or titles.
        - 'capitalize': Standardizes sentence-starts for descriptive fields.
    - Essential for ensuring that 'value_counts' accurately reflects the count of unique real-world items rather than just unique capitalization styles.
    
    Keywords: text normalization, case standardization, lowercase conversion, uppercase formatting, title case cleaning, string hygiene.
    """
    from mcp_servers.pandas_server.tools import text_ops
    return text_ops.str_case(file_path, column, case, output_path)

@mcp.tool()
def str_contains(file_path: str, column: str, pat: str, regex: bool = False, output_path: str = "") -> str:
    """CHECKS if string contains pattern. [ACTION]
    
    [RAG Context]
    A highly performant "Super Tool" for keyword-based boolean logic and data tagging. It allows the system to efficiently scan thousands of text entries to determine the presence of a specific substring or pattern. The result is a new boolean column (True/False), which can immediately be used for filtering datasets or for creating categorical "flags" (e.g., tagging all rows that mention a specific "Competitor Name" or "Urgent Status").
    
    How to Use:
    - 'pat': The text or pattern you are looking for.
    - 'regex': Set to True to use sophisticated pattern matching (e.g., searching for any digit sequence).
    - This is often used alongside 'filter_data' to isolate records that contain specific natural language keywords, making it an essential bridge between qualitative text and quantitative analysis.
    
    Keywords: keyword search, substring matching, boolean flag, data tagging, text filtering, pattern detection.
    """
    from mcp_servers.pandas_server.tools import text_ops
    return text_ops.str_contains(file_path, column, pat, regex, output_path)


# ==========================================
# 7. Statistical Operations
# ==========================================
# ==========================================
# 7. Statistical Operations
# ==========================================
@mcp.tool()
def calculate_zscore(file_path: str, columns: List[str], output_path: str) -> str:
    """CALCULATES Z-Scores for outlier detection. [ACTION]
    
    [RAG Context]
    A statistical "Super Tool" for anomaly detection and data normalization. The Z-score (standard score) quantifies exactly how many standard deviations a data point is from the sample mean. In competitive or financial data, this tool is the gold standard for identifying "extreme" values that are statistically unlikely to have occurred by chance. It transforms raw values—which might be in massive or tiny scales—into a common "sigma" scale, making them comparable across different features.
    
    How to Use:
    - Formula: `z = (x - μ) / σ`.
    - Interpretation: A score of 0 is exactly average. Most data falls between -2 and 2.
    - Standard Outlier Threshold: Values with a Z-score absolute value greater than 3.0 are typically considered significant outliers or potential errors.
    - Essential for fraud detection, quality control in manufacturing, and preparing data for distance-based machine learning algorithms like K-Means.
    
    Keywords: anomaly detection, standardization, gaussian distribution, sigma score, outlier identification, data scaling.
    """
    from mcp_servers.pandas_server.tools import stat_ops
    return stat_ops.calculate_zscore(file_path, columns, output_path)

@mcp.tool()
def rank_data(file_path: str, column: str, method: str = "average", ascending: bool = True, output_path: str = "") -> str:
    """ASSIGNS numerical ranks to values for competitive analysis. [ACTION]
    
    [RAG Context]
    An elite "Super Tool" for competitive positioning, benchmarking, and ordinal analysis. Unlike simple sorting, this tool calculates exactly where each row stands relative to the others (e.g., 1st place, 2nd place), which is essential for business KPIs like "Top Sales Reps" or "Fastest Growth Regions." It provides sophisticated handling for "ties," ensuring that you can control exactly how the system reacts when two records share the same value (e.g., should they both be '1' or should they split the difference?). This transformation adds a layer of actionable hierarchy to raw numerical data.
    
    How to Use:
    - 'method': 
        - 'min': Standard "1, 2, 2, 4" competition ranking.
        - 'dense': "1, 2, 2, 3" ranking where rank number doesn't skip after ties.
        - 'average': Splits the rank distance among ties (2.5, 2.5).
    - Perfect for creating learderboards, identifying quartiles manually, or preparing ordinal data for non-parametric statistical tests.
    
    Keywords: data ranking, leaderboard creation, competitive positioning, ordinal scale, tie-breaking strategy, benchmark ranking.
    """
    from mcp_servers.pandas_server.tools import stat_ops
    return stat_ops.rank_data(file_path, column, method, ascending, output_path)

@mcp.tool()
def quantile_stat(file_path: str, column: str, q: float) -> dict:
    """CALCULATES specific value at a distribution quantile. [DATA]
    
    [RAG Context]
    A precise "Super Tool" for statistical thresholding and Service Level Agreement (SLA) auditing. While the 'mean' provides an average, quantiles allow you to identify specific cut-off points within your data's distribution. For example, calculating the 0.95 quantile (95th percentile) for 'Response Time' tells you exactly the "worst-case" performance that 95% of users experience. This tool is fundamental for setting benchmarks, identifying "top 1%" performers, or defining the boundaries of what constitutes an "Outlier" in a given population.
    
    How to Use:
    - 'q': The quantile value (e.g., 0.5 for the Median, 0.25 for the first quartile, 0.99 for the extreme upper bound).
    - Use this to answer specific business questions like: "What is the maximum salary of the bottom 50%?" or "At what revenue level do we enter the top 10% of our clients?".
    
    Keywords: percentile calculation, distribution cut-off, median derivation, threshold analysis, benchmark setting, sla audit points.
    """
    from mcp_servers.pandas_server.tools import stat_ops
    return stat_ops.quantile(file_path, column, q)

@mcp.tool()
def correlation_matrix(file_path: str, method: str = "pearson") -> dict:
    """CALCULATES correlation matrix. [DATA]
    
    [RAG Context]
    An advanced "Super Tool" for identifying hidden relationships between variables. It constructs a square matrix that measures the linear strength and direction of the relationship between every pair of numeric columns in your dataset. This tool is fundamental for Exploratory Data Analysis (EDA) because it reveals which factors move together (positive correlation) and which move in opposite directions (negative correlation). It is the primary method for identifying "Multicollinearity," where variables are so similar that they provide redundant information.
    
    How to Use:
    - 1.0: Perfect positive relationship (as one goes up, the other goes up).
    - -1.0: Perfect negative relationship.
    - 0.0: No linear relationship.
    - Use 'pearson' (default) for linear relationships, or 'spearman' for non-linear, monotonic relationships.
    - Essential for scientific research, financial portfolio diversification, and feature selection in machine learning.
    
    Keywords: correlation analysis, relationship strength, multicollinerity, dependency metrics, pearson r, association test.
    """
    from mcp_servers.pandas_server.tools import stat_ops
    return stat_ops.correlation_matrix(file_path, method)

@mcp.tool()
def clip_data(file_path: str, columns: List[str], lower: Optional[float] = None, upper: Optional[float] = None, output_path: str = "") -> str:
    """CLIPS values to specified bounds. [ACTION]
    
    [RAG Context]
    A practical "Super Tool" for data constraint enforcement and signal boundary control. In many real-world datasets, extreme values (outliers) can occur due to measurement errors, data entry mistakes, or rare but highly influential events that can distort statistical summaries and cause machine learning models to overfit. This tool "clips" or "clamps" these values, forcing them to stay within a user-defined minimum (lower) and maximum (upper) boundary. This process, also known as "Winsorizing," preserves the data points but neutralizes their extreme influence, leading to more robust and stable analytical results.
    
    How to Use:
    - 'lower': Any value currently below this number will be replaced by this number.
    - 'upper': Any value currently above this number will be replaced by this number.
    - Essential for normalizing probability scores (ensuring they stay between 0 and 1) or for capping financial metrics where extreme spikes are considered non-representative noise.
    
    Keywords: data clamping, value capping, winsorization, range enforcement, outlier mitigation, boundary control, data normalization.
    """
    from mcp_servers.pandas_server.tools import stat_ops
    return stat_ops.clip_values(file_path, columns, lower, upper, output_path)


# ==========================================
# 8. Structural & Nested Data
# ==========================================
@mcp.tool()
def explode_list(file_path: str, column: str, output_path: str) -> str:
    """EXPLODES list-like column into rows. [ACTION]
    
    [RAG Context]
    A specialized "Super Tool" for data unnesting and relational normalization. Frequently, data extracted from NoSQL databases, JSON APIs, or multi-select web forms arrives with multiple values packed into a single cell as a Python list or array (e.g., a 'tags' column containing `["electronics", "sale", "new"]`). This tool "explodes" that single row into multiple distinct rows—one for each element in the list—while automatically duplicating all other field values from the original row. This transformation is a prerequisite for accurate counting, grouping, or filtering based on those individual list elements.
    
    How to Use:
    - Identify the column containing the nested lists.
    - After exploding, you can run 'value_counts' or 'group_by' on the target column to perform granular analysis on the individual items that were previously hidden within the lists.
    - Fundamental for processing marketing campaign tags, product feature lists, or log-file entries containing multiple error codes.
    
    Keywords: data unnesting, list-to-rows, hierarchical flattening, record expansion, relational normalization, array decomposition.
    """
    from mcp_servers.pandas_server.tools import struct_ops
    return struct_ops.explode_list(file_path, column, output_path)

@mcp.tool()
def flatten_json(file_path: str, column: str, output_path: str, sep: str = "_") -> str:
    """FLATTENS nested JSON column. [ACTION]
    
    [RAG Context]
    A critical "Super Tool" for bridging the gap between semi-structured JSON data and traditional tabular analysis. When modern APIs return nested structures—where a column contains a dictionary of sub-properties (e.g., a 'user_info' column containing `{"city": "NY", "zip": "10001"}`)—this tool unpacks those internal keys into individual, top-level columns in the dataset. This "flattening" process is required because standard analytical tools like regression models, scatter plots, and pivot tables cannot "see" inside nested JSON objects.
    
    How to Use:
    - 'column': The header containing the JSON objects/dictionaries.
    - 'sep': The separator used to name the new columns by concatenating the parent and child keys (e.g., `user_info_city`).
    - Essential for processing raw data from MongoDB exports, Segment/Amplitude events, or any modern REST API response that uses rich object hierarchies.
    
    Keywords: json unpacking, hierarchical flattening, schema normalization, nested data extraction, data mapping, flat table conversion.
    """
    from mcp_servers.pandas_server.tools import struct_ops
    return struct_ops.flatten_json(file_path, column, output_path, sep)

@mcp.tool()
def stack_data(file_path: str, level: int = -1, output_path: str = "") -> str:
    """STACKS columns into index levels (Wide to Long transformation). [ACTION]
    
    [RAG Context]
    A sophisticated "Super Tool" for hierarchical data reshaping and MultiIndex management. In advanced data modeling, you often have multiple levels of column headers (e.g., 'Year' at the top and 'Revenue/Profit' below it). "Stacking" is the process of compressing these column labels into the row index, effectively turning "wide" data into a "long" or "tall" format. This transformation is vital for normalizing data for databases, preparing datasets for specific types of visualization (like categorical bar charts), and enabling complex multi-dimensional filtering where you want to treat column headers as searchable data values.
    
    How to Use:
    - 'level': The specific level of the column hierarchy to move into the index (default is -1, the innermost level).
    - Use this tool when your columns represent "values" (like years 2020, 2021, 2022) rather than "variables," allowing you to unify them into a single 'Year' column.
    - Result is a more compact, vertically-aligned dataset that is easier to aggregate using 'group_by'.
    
    Keywords: wide-to-long, multi-index stacking, data pivoting, hierarchical reshaping, column-to-row, data normalization.
    """
    from mcp_servers.pandas_server.tools import struct_ops
    return struct_ops.stack_unstack(file_path, 'stack', level, output_path)

@mcp.tool()
def unstack_data(file_path: str, level: int = -1, output_path: str = "") -> str:
    """UNSTACKS index levels into column headers (Long to Wide transformation). [ACTION]
    
    [RAG Context]
    The inverse "Super Tool" to 'stack', designed for expanding hierarchical row indices back into a readable column-based structure. When data is in a "long" format—often the result of a grouping or stacking operation—it can be difficult for humans to read or for certain spreadsheet tools to process. Unstacking "pivots" a row-level index (like 'Region' or 'Product Category') back into the horizontal column headers. This is the primary method for creating "Side-by-Side" comparisons and for generating the final "Presentation-Ready" tables used in corporate dashboards and financial statements.
    
    How to Use:
    - 'level': The index level to move from the vertical rows to the horizontal columns.
    - Essential for turning a deep, multi-level summary (e.g., Sales by Region AND Year) into a cross-tabulated view (Rows=Region, Columns=Year).
    - Use this to broaden your dataset's dimensionality and create human-intuitive report layouts.
    
    Keywords: long-to-wide, data pivot, index-to-column, cross-tabulation, report expansion, horizontal reshaping.
    """
    from mcp_servers.pandas_server.tools import struct_ops
    return struct_ops.stack_unstack(file_path, 'unstack', level, output_path)

@mcp.tool()
def cross_join(left_path: str, right_path: str, output_path: str) -> str:
    """PERFORMS Cartesian product. [ACTION]
    
    [RAG Context]
    An intensive "Super Tool" for comprehensive combinatorial analysis and permutation generation. Unlike standard joins that look for matching keys, a 'cross_join' (Cartesian product) creates every possible combination of rows between two datasets. If File A has 10 rows and File B has 5 rows, the resulting File C will have exactly 50 rows. This tool is indispensable for scenarios where you need to model all potential outcomes or pairs, such as generating a complete list of all 'Products' multiplied by all 'Store Regions' to identify where sales data is missing.
    
    How to Use:
    - Warning: Resulting row counts can grow exponentially. (1,000 x 1,000 = 1,000,000 rows). Verify the source file shapes using the 'shape' tool before execution to avoid system memory exhaustion.
    - Perfect for creating experimental matrices, scenario testing, or building comprehensive "master lists" that cover all possible logistical permutations.
    
    Keywords: cartesian join, complete permutations, row combinations, combinatorial matrix, data expansion, matrix formation.
    """
    from mcp_servers.pandas_server.tools import struct_ops
    return struct_ops.cross_join(left_path, right_path, output_path)


# ==========================================
# 9. ML Preprocessing
# ==========================================
@mcp.tool()
def one_hot_encode(file_path: str, columns: List[str], output_path: str, drop_first: bool = False) -> str:
    """ENCODES categorical columns (One-Hot). [ACTION]
    
    [RAG Context]
    A mandatory "Super Tool" for preparing categorical data for mathematical machine learning models. Most advanced algorithms (such as Linear Regression, SVMs, or Neural Networks) require numerical inputs and cannot interpret raw text strings like "Red," "Green," or "Blue." This tool transforms each unique category into its own binary column (0 or 1). For example, a 'Color' column becomes three new columns: 'Color_Red', 'Color_Green', and 'Color_Blue'. If a row was "Red," the 'Color_Red' column is set to 1, while the others are 0.
    
    How to Use:
    - Specify the list of categorical columns to encode.
    - 'drop_first': Highly recommended for regression models to prevent the "Dummy Variable Trap" (multicollinearity) by discarding the first resulting dummy column.
    - This is the industry-standard way to convert non-numeric features into a format that a multi-dimensional model can navigate without assuming a false "rank" between the values.
    
    Keywords: dummy variables, flat encoding, feature engineering, machine learning preprocessing, categorical mapping, binarization.
    """
    from mcp_servers.pandas_server.tools import ml_ops
    return ml_ops.one_hot_encode(file_path, columns, output_path, drop_first)

@mcp.tool()
def bin_data(file_path: str, column: str, bins: Union[int, List[float]], labels: List[str] = None, method: str = 'cut', output_path: str = "") -> str:
    """BINS continuous data into intervals. [ACTION]
    
    [RAG Context]
    A powerful "Super Tool" for data discretization and feature simplification. Continuous variables (like 'Age', 'Price', or 'Temperature') often contain too much granular detail for certain types of analysis or modeling. This tool groups those raw numbers into discrete "buckets" or intervals (e.g., turning ages 0-100 into groups like 'Minor', 'Adult', and 'Senior'). By reducing the complexity of numeric data into meaningful categories, you can identify broader trends and make datasets more interpretable for both humans and classification algorithms.
    
    How to Use:
    - 'method':
        - 'cut': Creates bins of equal width (e.g., every 10 units).
        - 'qcut': Creates bins of equal size (each bin contains the same number of data points), useful for identifying quartiles or deciles.
    - 'labels': Optional list of names for your bins to make the output more descriptive.
    - Essential for performing "Cohort Analysis" or preparing data for "Decision Tree" models that thrive on discrete splits.
    
    Keywords: data bucketing, discretization, numeric grouping, cohort creation, feature engineering, interval cut.
    """
    from mcp_servers.pandas_server.tools import ml_ops
    return ml_ops.bin_data(file_path, column, bins, labels, method, output_path)

@mcp.tool()
def factorize_column(file_path: str, column: str, output_path: str) -> str:
    """ENCODES labels as integers. [ACTION]
    
    [RAG Context]
    A high-speed "Super Tool" for label encoding and ordinal data preparation. Unlike One-Hot encoding—which creates many new columns—this tool maps each unique categorical label in a column to a single, unique integer (e.g., 'Apple'=0, 'Banana'=1, 'Cherry'=2). This is the preferred method for tree-based machine learning models (like Random Forest, LightGBM, or XGBoost) because it keeps the feature space compact while still satisfying the algorithm's requirement for numerical input. It's also an efficient way to reduce the memory storage size of large categorical columns.
    
    How to Use:
    - Identify the column with text labels you wish to transform.
    - The transformation is purely mathematical; it does not imply a "ranking" (Cherry is 2, but not "twice as much" as Banana), so it is best used with non-parametric models that handle integer encodings natively.
    - Extremely useful for preparing "Target" variables (the thing you want to predict) in classification tasks.
    
    Keywords: label encoding, category-to-integer, label mapping, ordinal transform, feature compression, integer representation.
    """
    from mcp_servers.pandas_server.tools import ml_ops
    return ml_ops.factorize_col(file_path, column, output_path)


# ==========================================
# 10. Logic & Windowing
# ==========================================
# ==========================================
# 10. Logic & Windowing
# ==========================================
@mcp.tool()
def conditional_mask(file_path: str, condition: str, value_if_true: Any, value_if_false: Any, output_path: str, column: str) -> str:
    """APPLIES conditional logic (If/Else). [ACTION]
    
    [RAG Context]
    A high-speed "Super Tool" for vectorized logical operations and feature labeling. In standard programming, you might use a 'for' loop to check each row and assign a value, which is prohibitively slow for large datasets. This tool performs that logic across the entire column simultaneously (vectorized). It evaluates a boolean condition for every row and assigns 'Value A' if true and 'Value B' if false. It is the core engine for creating new categorical flags, implementing business rules, or cleaning data based on custom-defined thresholds.
    
    How to Use:
    - 'condition': Use standard Pandas query syntax (e.g., `revenue > expenditures`).
    - 'value_if_true' / 'value_if_false': The outcomes (e.g., "Profitable", "Loss").
    - 'column': The name of the new or existing header to update with these values.
    - Essential for making logic-based data decisions at scale without the overhead of row-by-row custom code.
    
    Keywords: vectorized if-else, conditional assignment, business logic, data flagging, feature marking, rule-based labeling.
    """
    from mcp_servers.pandas_server.tools import logic_ops
    return logic_ops.conditional_mask(file_path, condition, value_if_true, value_if_false, output_path, column)

@mcp.tool()
def isin_filter(file_path: str, column: str, values: List[Any], keep: bool = True, output_path: str = "") -> str:
    """FILTERS rows based on set membership (SQL 'IN' style). [ACTION]
    
    [RAG Context]
    A high-speed "Super Tool" for set-based data selection and exclusion. In complex data workflows, you often need to isolate records that belong to a specific list of "Allowed" or "Blocked" values (e.g., filtering for a specific list of 50 VIP Customers or excluding a list of 100 fraudulent IP addresses). This tool provides a vectorized way to perform this check across the entire dataset simultaneously, which is significantly more efficient than chain-linking multiple "equals" or "not equals" logic blocks. It is the direct equivalent of the SQL 'IN' clause.
    
    How to Use:
    - 'column': The header to check for matches.
    - 'values': The list of items to look for.
    - 'keep':
        - Set to True (default) to RETAIN rows where the value is in the list (Inclusion).
        - Set to False to DISCARD rows where the value is in the list (Exclusion).
    - Perfect for cohort analysis, whitelist/blacklist enforcement, and targeted data extraction.
    
    Keywords: set membership, list filtering, sql in, inclusion criteria, exclusion list, whitelist blacklist, row selection.
    """
    from mcp_servers.pandas_server.tools import logic_ops
    return logic_ops.isin_filter(file_path, column, values, keep, output_path)

@mcp.tool()
def compare_datasets(left_path: str, right_path: str) -> dict:
    """COMPARES two datasets to identify differences and changes. [DATA]
    
    [RAG Context]
    A critical "Super Tool" for data auditing, regression testing, and version control. When working with iterative data pipelines, it is essential to know exactly what changed between two versions of the same file. This tool performs a side-by-side structure and value comparison, identifying new rows (Target vs Source), deleted rows, and rows where the values in specific columns have drifted. It acts as a "Data Diff" engine, providing a clear audit trail of additions, subtractions, and modifications.
    
    How to Use:
    - 'left_path' & 'right_path': The two files you wish to compare.
    - Use this after a complex transformation to verify that the changes were exactly as expected (e.g., "Did my filter actually remove the 10 rows I intended?").
    - Indispensable for tracking historical changes in master records, price lists, or configuration tables where data integrity is paramount.
    
    Keywords: data diff, change detection, regression audit, version comparison, parity check, delta analysis, dataset tracking.
    """
    from mcp_servers.pandas_server.tools import logic_ops
    return logic_ops.compare_datasets(left_path, right_path)

@mcp.tool()
def ewm_calc(file_path: str, span: float, agg: str, columns: List[str], output_path: str) -> str:
    """CALCULATES Exponential Weighted (EW) statistics for time-series smoothing. [ACTION]
    
    [RAG Context]
    A specialized "Super Tool" for financial analysis and technical trend detection. Unlike standard moving averages—which treat all data points in a window equally—Exponential Weighted Moving (EWM) statistics assign significantly more weight to the most recent observations while allowing older data to "decay" over time. This makes the resulting metric much more responsive to sudden shifts in momentum (like stock price breakouts or server latency spikes) while still smoothing out high-frequency "noise." It is a fundamental tool for building technical indicators like the EMA (Exponential Moving Average).
    
    How to Use:
    - 'span': The decay parameter (e.g., a 20-period EMA).
    - 'agg': The statistic to calculate (e.g., 'mean', 'std', 'var').
    - Essential for algorithmic trading, real-time telemetry monitoring, and any scenario where "current state" is more important than "historical average."
    
    Keywords: exponential smoothing, ema calculation, trend detection, technical analysis, momentum smoothing, decay weighting.
    """
    from mcp_servers.pandas_server.tools import window_ops
    return window_ops.ewm_calc(file_path, span, agg, columns, output_path)

@mcp.tool()
def expanding_calc(file_path: str, agg: str, columns: List[str], output_path: str) -> str:
    """CALCULATES cumulative (Expanding) statistics over time. [ACTION]
    
    [RAG Context]
    A vital "Super Tool" for cumulative performance tracking and running-total analysis. Unlike moving windows that "slide" across the data, an expanding window starts at the very first record and grows with every subsequent row. This means the result at row 'N' is the aggregation of ALL data from the beginning of time up to that point. This tool is the engine for calculating "Year-to-Date" (YTD) totals, cumulative revenue growth, and lifetime customer value (LTV) metrics.
    
    How to Use:
    - Result at row 100 is the mean/sum/min/max of rows 0 through 100.
    - Ideal for tracking the progression of a metric over its entire lifespan to identify long-term milestones and historical peaks.
    
    Keywords: cumulative sum, running total, expanding average, year-to-date metrics, lifetime value, growing window.
    """
    from mcp_servers.pandas_server.tools import window_ops
    return window_ops.expanding_calc(file_path, agg, columns, output_path)

@mcp.tool()
def pct_change(file_path: str, periods: int, columns: List[str], output_path: str) -> str:
    """CALCULATES percentage change over periods. [ACTION]
    
    [RAG Context]
    A specialized "Super Tool" for measuring growth rates and relative performance. In business and finance, understanding the absolute change in a value (the 'diff') is often less descriptive than understanding the percentage change relative to the starting point. This tool calculates exactly that—the fractional increase or decrease between the current observation and an observation 'N' periods in the past. It is the primary engine for building "YoY" (Year-over-Year) or "MoM" (Month-over-Month) growth reports that form the backbone of corporate KPIs and stock market analysis.
    
    How to Use:
    - 'periods': The lookback interval (e.g., set to 1 for day-over-day change, or 7 for week-over-week change in a daily dataset).
    - Formula: `(Current - Prior) / Prior`.
    - Essential for identifying momentum, seasonal growth bursts, or sudden downturns in metrics like active users, quarterly revenue, or inventory turnover speed.
    
    Keywords: percentage growth, ROI calculation, rate of change, relative difference, growth tracking, momentum metrics.
    """
    from mcp_servers.pandas_server.tools import window_ops
    return window_ops.pct_change(file_path, periods, columns, output_path)


# ==========================================
# 11. Math & Scientific (New)
# ==========================================
@mcp.tool()
def apply_math(file_path: str, columns: List[str], func: str, output_path: str) -> str:
    """APPLIES mathematical functions. [ACTION]
    
    [RAG Context]
    A versatile "Super Tool" for advanced mathematical feature engineering and data transformation. While standard arithmetic is handled by basic scripts, this tool provides access to high-performance vectorized NumPy operations. It allows you to apply non-linear transformations like logarithmic scaling, square roots, or exponentials to entire columns simultaneously. These operations are vital for "normalizing" data distributions that are highly skewed (e.g., household income or city populations) so they can be effectively processed by linear models.
    
    How to Use:
    - 'func':
        - 'log': Natural log. Great for compressing large numeric ranges.
        - 'exp': Exponential.
        - 'sqrt': Square root.
        - 'abs': Absolute value (removes negative signs).
        - 'round': Standard rounding to the nearest integer.
    - Transformation is applied selectively to the 'columns' you specify, ensuring that non-numeric or unrelated data remains untouched.
    
    Keywords: mathematical transform, nonlinear scaling, data compression, vectorized math, distribution normalization, log-scale engineering.
    """
    from mcp_servers.pandas_server.tools import math_ops
    return math_ops.apply_math(file_path, columns, func, output_path)

@mcp.tool()
def normalize_minmax(file_path: str, columns: List[str], output_path: str) -> str:
    """SCALES data to [0, 1] range. [ACTION]
    
    [RAG Context]
    A fundamental "Super Tool" for feature scaling and data uniformity. In modern data science, features often have vastly different scales—for example, 'Income' might range from 0 to 1,000,000, while 'Age' ranges from 0 to 100. This disparity can cause distance-based algorithms (like K-Nearest Neighbors) or gradient-based models (like Neural Networks) to focus solely on the high-magnitude columns. Min-Max normalization linearly compresses all values into a fixed range between 0.0 and 1.0, ensuring that every feature has an equal "voice" in the final model result.
    
    How to Use:
    - Formula: `x_scaled = (x - x_min) / (x_max - x_min)`.
    - This is the standard normalization technique when you know the boundaries of your data and want to preserve the relative distance between points without making assumptions about their distribution.
    - Mandatory for weight-sensitive algorithms and image data processing.
    
    Keywords: minmax scaling, data normalization, feature weighting, range compression, zero-to-one scale, data science preparation.
    """
    from mcp_servers.pandas_server.tools import math_ops
    return math_ops.normalize_minmax(file_path, columns, output_path)

@mcp.tool()
def standardize_scale(file_path: str, columns: List[str], output_path: str) -> str:
    """SCALES data to Mean=0, Std=1. [ACTION]
    
    [RAG Context]
    A robust "Super Tool" for statistical data standardization. This tool implements the "StandardScaler" technique, which transforms numeric columns so that they have a Mean of 0.0 and a Standard Deviation of 1.0. Unlike Min-Max scaling, which forces data into a 0-to-1 box, Standardization preserves the underlying shape of the distribution (like the Bell Curve) while centering it. This is the preferred method for algorithms that assume data is normally distributed, such as Principal Component Analysis (PCA) or Linear Discriminant Analysis (LDA).
    
    How to Use:
    - Formula: `x_standardized = (x - mean) / std_dev`.
    - Resulting values typically fall between -3.0 and 3.0.
    - Standardizing your features prevents "Magnitude Bias," where columns with larger numbers disproportionately influence the behavior of your predictive models.
    
    Keywords: standard scaling, z-score normalization, distribution centering, gaussian preparation, statistical scaling, feature standardization.
    """
    from mcp_servers.pandas_server.tools import math_ops
    return math_ops.standardize_scale(file_path, columns, output_path)

@mcp.tool()
def calc_stats_vector(file_path: str, columns: List[str], func: str) -> dict:
    """CALCULATES mathematical vector norms (L1/L2 magnitude). [DATA]
    
    [RAG Context]
    An advanced "Super Tool" for mathematical magnitude calculation and distance-based analysis. In multi-dimensional data, you often need to calculate the "length" or "distance" of a row's values from a zero point. This tool calculates standard vector norms: the L1 Norm (Manhattan distance, sum of absolute values) and the L2 Norm (Euclidean distance, square root of the sum of squares). These metrics are fundamental for "Error Analysis" (calculating the magnitude of residuals) and for preparing data for machine learning algorithms that rely on vector similarity.
    
    How to Use:
    - 'func': 'norm_l1' (Taxicab distance) or 'norm_l2' (Straight-line magnitude).
    - Use this to quantify the overall "strength" or "error volume" across a group of related numeric features.
    
    Keywords: vector magnitude, euclidean distance, l1 norm, l2 norm, mathematical distance, vector analysis.
    """
    from mcp_servers.pandas_server.tools import math_ops
    return math_ops.calc_stats_vector(file_path, columns, func)


# ==========================================
# 12. Quality & Validation (New)
# ==========================================
@mcp.tool()
def validate_schema(file_path: str, required_columns: List[str], types: Optional[Dict[str, str]] = None) -> dict:
    """VALIDATES dataset schema. [DATA]
    
    [RAG Context]
    A robust "Super Tool" for data governance and pipeline defensive programming. In automated systems, "Schema Drift"—where the structure of incoming data changes unexpectedly—is one of the most common causes of system failure. This tool acts as a gatekeeper, verifying that a dataset contains all mandatory columns and, optionally, that those columns match the expected data types (e.g., ensuring a 'Price' column represents floats and not text). By running this validation at the start of a workflow, you ensure that all subsequent analytical tools will function correctly on the provided data.
    
    How to Use:
    - 'required_columns': A list of headers that MUST be present.
    - 'types': An optional mapping (e.g., `{"id": "int64", "email": "object"}`) to enforce strict data type compliance.
    - Essential for production-grade pipelines where data originates from external sources that lack strict relational constraints (like CSV or JSON exports).
    
    Keywords: schema enforcement, data contract, structural validation, pipeline safety, data integrity check, schema drift detection.
    """
    from mcp_servers.pandas_server.tools import quality_ops
    return quality_ops.validate_schema(file_path, required_columns, types)

@mcp.tool()
def check_constraints(file_path: str, constraints: List[str]) -> dict:
    """CHECKS complex data quality and business logic constraints. [DATA]
    
    [RAG Context]
    A sophisticated "Super Tool" for automated data auditing and business rule enforcement. While schema validation checks the format, 'check_constraints' verifies the actual *content* against logical rules (e.g., ensuring 'Age' is never negative, 'Discount' is never greater than 1.0, or 'Ship_Date' is after 'Order_Date'). This tool performs high-speed vectorized checks across the entire dataset and returns a detailed failure report, allowing you to catch "Silent Data Corruption" or domain violations before they pollute downstream reports or financial calculations.
    
    How to Use:
    - 'constraints': A list of boolean expressions (e.g., `["price > 0", "category.isin(['A', 'B'])"]`).
    - Use this during the data ingestion phase to "gate" incoming files; if they fail the logical constraints, they are marked as "High Risk" for further human review.
    
    Keywords: data audit, logical validation, business rules, constraint checking, domain integrity, data sanitation check.
    """
    from mcp_servers.pandas_server.tools import quality_ops
    return quality_ops.check_constraints(file_path, constraints)

@mcp.tool()
def drop_outliers(file_path: str, columns: List[str], factor: float = 1.5, output_path: str = "") -> str:
    """REMOVES outliers using IQR. [ACTION]
    
    [RAG Context]
    An automated "Super Tool" for statistical data cleaning and noise reduction. It uses the Interquartile Range (IQR) method—a robust measure of variability—to identify rows that are numerically deviant from the majority of the distribution. It calculates the range between the 25th (Q1) and 75th (Q3) percentiles; any value that falls significantly outside this range (typically 1.5 times the IQR distance) is flagged and removed. This process is vital for cleaning sensors data, financial transactions, or survey results where extreme, singular events would otherwise skew the entire analytical result.
    
    How to Use:
    - 'columns': The specific numeric headers to scan for outliers.
    - 'factor': The sensitivity of the filter. A factor of 1.5 (standard) captures "mild" outliers. Increasing to 3.0 (Tukey's Fences) ensures that only truly extreme "black swan" events are discarded.
    - Result is a "cleaner" version of the dataset that more accurately represents the typical behavior of the population.
    
    Keywords: outlier removal, iqr filtering, data cleaning, statistical noise reduction, anomaly excision, robust statistics.
    """
    from mcp_servers.pandas_server.tools import quality_ops
    return quality_ops.remove_outliers_iqr(file_path, columns, factor, output_path)

@mcp.tool()
def drop_empty_cols(file_path: str, threshold: float = 1.0, output_path: str = "") -> str:
    """REMOVES sparse or completely empty columns from the dataset. [ACTION]
    
    [RAG Context]
    A critical "Super Tool" for data structural sanitation and dimensionality reduction. In real-world data collection, it is common to have columns that are legacy artifacts or were never populated, resulting in a high percentage of "NaN" (Not a Number) or Null values. Keeping these sparse columns increases memory usage and can confuse analytical models. This tool identifies and discards any column that fails to meet a specified "Content Threshold," ensuring that your final dataset contains only active, data-rich features.
    
    How to Use:
    - 'threshold': The proportion of Null values allowed. 
        - 1.0 (default): Only drops columns that are 100% empty.
        - 0.5: Drops any column where more than 50% of the rows are missing data.
    - Essential for cleaning up automated system exports and for reducing "noise" before performing high-dimensional statistical analysis or machine learning.
    
    Keywords: data sparse cleanup, empty column removal, dimensionality reduction, feature selection, null thresholding, data sanitation.
    """
    from mcp_servers.pandas_server.tools import quality_ops
    return quality_ops.drop_empty_cols(file_path, threshold, output_path)


# ==========================================
# 13. NLP Lite (New)
# ==========================================
@mcp.tool()
def tokenize_text(file_path: str, column: str, output_path: str) -> str:
    """TOKENIZES text column. [ACTION]
    
    [RAG Context]
    A foundational "Super Tool" for Natural Language Processing (NLP) and text analytics. Raw human language is inherently unstructured; computers cannot "calculate" on a paragraph of text directly. Tokenization is the process of breaking that raw string down into its constituent "tokens"—typically individual words, though it can also include symbols or sub-word units. This tool transforms a single text column into a column of structured lists, which is the mandatory first step before generating word counts, performing sentiment analysis, or embedding text for vector search systems like RAG.
    
    How to Use:
    - Target the specific text column (e.g., 'customer_feedback' or 'incident_description').
    - The output creates a structured representation where each word is isolated, enabling the system to understand the "vocabulary" of your dataset.
    - Ideal for prepping data for search index generation or for training custom topic-modeling algorithms.
    
    Keywords: text tokenization, nlp preprocessing, word segmentation, lexer, linguistic parsing, text mining preparation.
    """
    from mcp_servers.pandas_server.tools import nlp_ops
    return nlp_ops.tokenize_text(file_path, column, output_path)

@mcp.tool()
def word_count(file_path: str, column: str, output_path: str) -> str:
    """EXTRACTS textual complexity metrics (Word/Char counts). [ACTION]
    
    [RAG Context]
    A high-speed "Super Tool" for quantitative natural language analysis and content auditing. While reading text provides qualitative insight, calculating the "volume" of text provides essential quantitative data for modeling. This tool analyzes every entry in a text column to determine the total word count, character count, and unique word count (lexical richness). These metrics are foundational for identifying "Low-Quality" entries, segmenting documents by length, and preparing data for linguistic complexity analysis.
    
    How to Use:
    - 'column': The header containing the text strings to analyze.
    - The tool generates three new numeric columns based on the original content, enabling you to immediately filter or sort your dataset by "Document Length" or "Vocabulary Size."
    - Ideal for auditing customer support tickets, social media sentiment data, or any long-form textual feedback.
    
    Keywords: text complexity, word counting, document length, lexical richness, vocabulary audit, linguistic metrics, quantitative nlp.
    """
    from mcp_servers.pandas_server.tools import nlp_ops
    return nlp_ops.count_words(file_path, column, output_path)

@mcp.tool()
def generate_ngrams(file_path: str, column: str, n: int, output_path: str) -> str:
    """GENERATES text N-Grams for contextual phrase analysis. [ACTION]
    
    [RAG Context]
    A sophisticated "Super Tool" for capturing linguistic context and phrase-based patterns. Standard word counting (Unigrams) misses the relationship between words (e.g., "not good" vs "good"). N-Grams solve this by extracting sequences of 'N' consecutive words. Bigrams (N=2) and Trigrams (N=3) allow the system to identify common multi-word phrases, idioms, and entity relationships within your text data. This is a mandatory step for building high-quality search indices, performing "Next Word Prediction" analysis, and for advanced sentiment engines that need to understand contextual negation.
    
    How to Use:
    - 'n': The number of consecutive words in each phrase (e.g., 2 for Bigrams).
    - Use this tool to transform a column of sentences into a column of structured phrase-lists.
    - Perfect for "Key Phrase Extraction" and for identifying the most common multi-word concepts in customer feedback or technical documentation.
    
    Keywords: bigrams, trigrams, phrase extraction, sequence mining, linguistic context, contextual analysis, n-gram generation.
    """
    from mcp_servers.pandas_server.tools import nlp_ops
    return nlp_ops.generate_ngrams(file_path, column, n, output_path)


# ==========================================
# 14. Feature Engineering (New)
# ==========================================
@mcp.tool()
def create_interactions(file_path: str, features: List[str], operations: List[str], output_path: str) -> str:
    """CREATES interaction features to capture variable synergy. [ACTION]
    
    [RAG Context]
    An elite "Super Tool" for automated feature engineering and relationship discovery. In complex systems, the relationship between two variables is often multi-dimensional—for example, 'Price' and 'Quantity' individually are useful, but their product ('Revenue') is far more descriptive. This tool automatically generates new "Interaction Features" by combining existing columns through mathematical operations. It is the core engine for creating "Derived Metrics" and for enabling machine learning models to capture non-additive relationships (synergies) between independent features.
    
    How to Use:
    - 'features': The list of columns to combine.
    - 'operations': 'mul' (*), 'div' (/), 'add' (+), 'sub' (-).
    - If you pass `features=["price", "units"]` and `operations="mul"`, the tool creates a new `price_mul_units` column.
    - Indispensable for building sophisticated financial models and for increasing the predictive power of linear algorithms.
    
    Keywords: feature interactions, derived metrics, synergy features, formula generation, mathematical combinations, feature cross.
    """
    from mcp_servers.pandas_server.tools import feature_ops
    return feature_ops.create_interactions(file_path, features, operations, output_path)

@mcp.tool()
def polynomial_features(file_path: str, columns: List[str], degree: int, output_path: str) -> str:
    """CREATES non-linear polynomial features for advanced modeling. [ACTION]
    
    [RAG Context]
    A high-level "Super Tool" for statistical expansion and non-linear feature engineering. In many natural and financial systems, the relationship between variables is not a simple straight line (Linear). Polynomial expansion generates new features by raising existing columns to higher powers (e.g., x^2, x^3) and creating interaction terms between them. This process allows simple linear models (like Linear Regression) to capture complex, curved relationships and multi-variable dependencies, significantly increasing their predictive accuracy on non-linear datasets.
    
    How to Use:
    - 'degree': The maximum power to raise the features to (e.g., degree=2 creates squares and two-way interactions).
    - 'columns': The numeric headers to expand.
    - Essential for modeling accelerating trends, physical phenomena (like gravity or drag), and for providing simpler algorithms with the "flexibility" typically associated with more complex neural networks.
    
    Keywords: polynomial expansion, non-linear features, power terms, basis expansion, feature engineering, higher-degree modeling.
    """
    from mcp_servers.pandas_server.tools import feature_ops
    return feature_ops.polynomial_features(file_path, columns, degree, output_path)


# ==========================================
# 15. Chain Executor (Super Tool)
# ==========================================
@mcp.tool()
def execute_chain(initial_file_path: str, steps: List[Dict[str, Any]], final_output_path: Optional[str] = None) -> Dict[str, Any]:
    """EXECUTES a sequence of Pandas tools as a single atomic operation. [ACTION] [SUPER TOOL]
    
    [RAG Context]
    The ultimate "Grand-Master Super Tool" for sophisticated data engineering and complex analytical workflows. Individually, Pandas tools are powerful; combined, they form a complete, autonomous data factory. This tool allows the system to define a multi-stage "processing pipeline"—such as loading a dataset, filtering it, grouping by region, calculating growth rates, and finally sorting results—and execute the entire sequence in memory. This eliminates the massive overhead and file I/O bottlenecks that occur when saving intermediate CSV files at every step, making it the most efficient way to perform deep-dive data investigations and generate complex executive reports.
    
    How to Use:
    - 'steps': A structured list of operations to perform in order. Each step must specify the 'tool' (e.g., 'filter_data', 'group_by') and its corresponding 'args'.
    - The system automatically passes the output of one step as the input to the next, maintaining a seamless chain of custody for the data.
    - 'final_output_path': If provided, the end result of the entire chain is persisted to this location.
    - Essential for implementing enterprise-grade "Data Jigs" and automated ETL (Extract, Transform, Load) processes within the Kea ecosystem.
    
    Keywords: sequence execution, pivot chain, atomic processing, etl pipeline, data factory, multi-stage analysis, in-memory workflow.
    """
    from mcp_servers.pandas_server.tools import chain_ops
    return chain_ops.execute_chain(initial_file_path, steps, final_output_path)


# ==========================================
# 16. Bulk Operations (New)
# ==========================================
@mcp.tool()
def bulk_read_datasets(urls: List[str]) -> Dict[str, Any]:
    """READS and downloads multiple datasets from remote URLs. [DATA] [SUPER TOOL]
    
    [RAG Context]
    A heavy-duty "Super Tool" for large-scale data ingestion and remote resource synchronization. In modern cloud environments, data is rarely located in a single file; it is often distributed across multiple URLs or partitioned into several compressed archives. This tool acts as an automated "Data Harvester," capable of concurrently downloading multiple CSV, JSON, or ZIP files (containing CSVs) from the web. It handles the low-level networking, decompression, and initial parsing, providing a unified status report that identifies which resources were successfully retrieved and which encountered errors.
    
    How to Use:
    - 'urls': A list of direct download links to the datasets.
    - The tool returns a comprehensive metadata dictionary including local temporary paths, success flags, and row counts for each successfully ingested resource.
    - Fundamental for building "Data Lakes" and for initializing large-scale analytical projects that require the aggregation of diverse external data sources.
    
    Keywords: batch ingestion, multi-file download, remote data harvester, internet data source, zip decompression, automated data acquisition.
    """
    from mcp_servers.pandas_server.tools import bulk_ops
    return bulk_ops.bulk_read_datasets(urls)

@mcp.tool()
def merge_datasets_bulk(file_paths: List[str], on: str, how: str = "inner", output_path: str = "") -> str:
    """MERGES multiple dataframes. [ACTION]
    
    [RAG Context]
    A high-capacity "Super Tool" for large-scale data consolidation. While standard 'merge' operations work on two files, this tool enables the simultaneous fusion of an entire list of datasets into a single master record. It iteratively applies relational join logic, ensuring that all records across all provided files are aligned on a central key (e.g., 'employee_id' or 'transaction_hash'). This is an essential tool for "Corporate Memory" tasks, such as combining monthly financial snapshots from various departments into a single annual consolidation file for enterprise reporting.
    
    How to Use:
    - 'file_paths': A list of absolute paths to the files you wish to merge.
    - 'on': The common column header that exists across all files.
    - 'how': The join strategy (e.g., 'inner' to keep only records in all files, or 'outer' for a complete union).
    - Perfect for rebuilding a unified view from scattered, partitioned, or historical data backups.
    
    Keywords: multi-file merge, data consolidation, relational fusion, batch join, master record creation, dataset assembly.
    """
    from mcp_servers.pandas_server.tools import bulk_ops
    return bulk_ops.merge_datasets_bulk(file_paths, on, how, output_path)


# ==========================================
# 17. Pipeline Operations (New)
# ==========================================
@mcp.tool()
def clean_dataset_auto(file_path: str, output_path: str) -> str:
    """CLEANS dataset automatically. [ACTION]
    
    [RAG Context]
    The definitive "Super-Cleaning" tool for rapid data preparation and sanitation. This tool executes a standardized, professional-grade pipeline that addresses the most common "data rot" issues in one pass. It standardizes headers, removes leading/trailing whitespace, drops completely empty columns, intelligently imputes missing values, parses detectable date formats, and flags statistical outliers. It is designed to transform "raw" and "dirty" exports into "analysis-ready" data with minimal human intervention, making it the perfect first step for any new data investigation.
    
    How to Use:
    - Simply provide the source file and an output destination.
    - This is the "Easy Button" for data engineering; use it whenever you receive a new file from an untrusted or heterogeneous source to ensure a baseline level of data quality before performing deeper analysis.
    
    Keywords: automated cleaning, data sanitation, easy prep, intelligent imputation, cleaning pipeline, baseline quality.
    """
    from mcp_servers.pandas_server.tools import pipeline_ops
    return pipeline_ops.clean_dataset_auto(file_path, output_path)

@mcp.tool()
def generate_profile_report(file_path: str, output_path: str) -> str:
    """GENERATES HTML profile report for deep data auditing. [DATA]
    
    [RAG Context]
    An elite "Super Tool" for comprehensive data auditing and Exploratory Data Analysis (EDA). This tool generates a rich, interactive HTML report that provides a 360-degree view of your dataset. Unlike simple summary statistics, this report includes missing value alerts, correlation heatmaps, detailed histograms for every numeric column, and lexical analysis for text fields. It is the gold standard for "Data Profiling," allowing analysts and agents to instantly spot issues with data quality, skewness, or potential biases before a single model is built or decision is made.
    
    How to Use:
    - Provide the path to your dataset.
    - The tool generates a standalone HTML file at the 'output_path'. Open this file in a browser to explore the data interactively.
    - Mandated for the initial "Discovery Phase" of any new project to ensure thorough understanding of the data's characteristics.
    
    Keywords: data profiling, eda report, audit dashboard, quality heatmap, distribution audit, interactive analysis, data summary.
    """
    from mcp_servers.pandas_server.tools import pipeline_ops
    return pipeline_ops.generate_profile_report(file_path, output_path)

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class PandasServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []

