
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
    Facilitates file format migration, typically used to optimize for storage or performance. 
    
    How to Use:
    - Convert a slow CSV to a fast, compressed Parquet file for high-performance querying.
    - Export a technical JSON/Parquet file to Excel for human-readable reporting.
    
    Arguments:
    - source_path (str): Original file.
    - dest_path (str): Target file location.
    - dest_format (str): 'csv', 'excel', 'parquet', 'json'.
    
    Keywords: format conversion, csv to parquet, export to excel, save as, data migration.
    """
    from mcp_servers.pandas_server.tools import io_ops
    return io_ops.convert_dataset(source_path, dest_path, source_format, dest_format)

@mcp.tool()
def get_dataset_info(file_path: str) -> dict:
    """GETS detailed dataset metadata. [DATA]
    
    [RAG Context]
    Retrieves low-level technical metadata about a dataset without loading the entire content into memory (where possible).
    
    How to Use:
    - Returns precise row counts, column names, null counts per column, and memory usage.
    - Use this to gauge the "heaviness" of a dataset before performing complex transformations.
    
    Arguments:
    - file_path (str): Path to the dataset.
    
    Keywords: file info, memory usage, row count, null check, dataset size.
    """
    from mcp_servers.pandas_server.tools import io_ops
    return io_ops.get_file_info(file_path)


# ==========================================
# 2. Inspection Operations
# ==========================================
@mcp.tool()
def head(file_path: str, n: int = 5) -> list:
    """GETS first n rows of dataset. [DATA]
    
    [RAG Context]
    A quick-glance "Super Tool" for data validation. It retrieves the first 'n' records of any supported dataset (CSV, Excel, Parquet), providing an immediate visual profile of the content, column alignment, and initial data quality without loading the entire file.
    
    How to Use:
    - 'n': Adjust based on how much data you need to "see" (default is 5).
    - Excellent for verifying that headers were parsed correctly and that the data matches your expectations before running heavy analytical pipelines.
    
    Keywords: data preview, top rows, head operation, browse table, initial check.
    """
    from mcp_servers.pandas_server.tools import inspection_ops
    return inspection_ops.inspect_head(file_path, n)

@mcp.tool()
def tail(file_path: str, n: int = 5) -> list:
    """GETS last n rows of dataset. [DATA]
    
    [RAG Context]
    Returns the bottom 'n' rows of the file.
    
    How to Use:
    - Check if the data ends correctly or contains trailing aggregate rows.
    
    Arguments:
    - file_path (str): Target file.
    - n (int): Number of rows.
    
    Keywords: data preview, bottom rows, tail operation, end of file.
    """
    from mcp_servers.pandas_server.tools import inspection_ops
    return inspection_ops.inspect_tail(file_path, n)

@mcp.tool()
def columns(file_path: str) -> list:
    """GETS list of column names. [DATA]
    
    [RAG Context]
    Returns a simple list of strings representing the headers/keys of the dataset.
    
    How to Use:
    - Use this before performing 'select_columns' or 'filter_data' to ensure you have the correct spelling and case of column names.
    
    Keywords: list headers, schema names, keys, field list.
    """
    from mcp_servers.pandas_server.tools import inspection_ops
    return inspection_ops.inspect_columns(file_path)

@mcp.tool()
def dtypes(file_path: str) -> dict:
    """GETS column data types. [DATA]
    
    [RAG Context]
    Provides a mapping of column names to their underlying Pandas data types.
    
    How to Use:
    - Use to verify if columns were parsed correctly (e.g., ensuring a 'date' column isn't being treated as an 'object' or 'string').
    - Returns types like 'int64', 'float64', 'datetime64[ns]', 'bool', 'object'.
    
    Keywords: schema types, data classification, column formats, dtype check.
    """
    from mcp_servers.pandas_server.tools import inspection_ops
    return inspection_ops.inspect_dtypes(file_path)

@mcp.tool()
def describe(file_path: str) -> dict:
    """CALCULATES summary statistics. [DATA]
    
    [RAG Context]
    Generates descriptive statistics that summarize the central tendency, dispersion, and shape of a dataset's distribution, excluding NaN values.
    
    How to Use:
    - For numeric data: Returns count, mean, std (standard deviation), min, 25%, 50% (median), 75%, and max.
    - Essential for initial Exploratory Data Analysis (EDA) to find outliers or data range issues.
    
    Keywords: statistics summary, mean and median, standard deviation, quartiles, data distribution.
    """
    from mcp_servers.pandas_server.tools import inspection_ops
    return inspection_ops.inspect_describe(file_path)

@mcp.tool()
def value_counts(file_path: str, column: str, n: int = 10) -> dict:
    """COUNTS unique values in a column. [DATA]
    
    [RAG Context]
    Returns a frequency count of unique values in a specific column, sorted in descending order.
    
    How to Use:
    - Excellent for categorical columns (e.g., 'country', 'status', 'category') to see which values are most common.
    - Set 'n' to limit the results to the top most frequent items.
    
    Arguments:
    - file_path (str): Target file.
    - column (str): Name of the column to analyze.
    
    Keywords: frequency count, distinct values, distribution, categorical analysis.
    """
    from mcp_servers.pandas_server.tools import inspection_ops
    return inspection_ops.inspect_value_counts(file_path, column, n)

@mcp.tool()
def shape(file_path: str) -> tuple:
    """GETS dataset dimensions (rows, cols). [DATA]
    
    [RAG Context]
    Returns a tuple representing the dimensionality of the DataFrame.
    
    Shape Format: (rows, columns).
    
    Keywords: dimensionality, size, row count, column count.
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
    Selects a subset of rows from the dataset based on a boolean expression. 
    
    How to Use:
    - Uses the standard Pandas 'query' engine syntax.
    - Example queries:
        - `age > 30`
        - `status == "active" and score >= 80`
        - `city in ["London", "Paris"]`
    - The filtered result is saved to 'output_path'.
    
    Arguments:
    - query (str): The boolean condition.
    - output_path (str): Where to save the resulting file.
    
    Keywords: subset rows, boolean indexing, search data, conditional selection.
    """
    from mcp_servers.pandas_server.tools import core_ops
    return core_ops.filter_data(file_path, query, output_path)

@mcp.tool()
def select_columns(file_path: str, columns: List[str], output_path: str) -> str:
    """KEEPS only specified columns. [ACTION]
    
    [RAG Context]
    Reduces the width of the dataset by retaining only the listed columns.
    
    How to Use:
    - Essential for cleaning up large datasets with many unnecessary features.
    - Improves processing speed and reduces memory usage for downstream tools.
    
    Arguments:
    - columns (List[str]): List of headers to keep.
    
    Keywords: column selection, feature subset, drop columns, projection.
    """
    from mcp_servers.pandas_server.tools import core_ops
    return core_ops.select_columns(file_path, columns, output_path)

@mcp.tool()
def sort_data(file_path: str, by: Union[str, List[str]], ascending: bool, output_path: str) -> str:
    """SORTS dataset by column(s). [ACTION]
    
    [RAG Context]
    Reorders the rows in the dataset based on the values in one or more columns.
    
    How to Use:
    - Sort numerically (prices, dates) or alphabetically (names).
    - Can sort by multiple columns (e.g., sort by 'category' then by 'price').
    
    Arguments:
    - by: Column name(s) to sort by.
    - ascending: True for A-Z / 1-10, False for Z-A / 10-1.
    
    Keywords: ordering, reorder rows, sorting, rank order.
    """
    from mcp_servers.pandas_server.tools import core_ops
    return core_ops.sort_data(file_path, by, ascending, output_path)

@mcp.tool()
def drop_duplicates(file_path: str, subset: Optional[List[str]] = None, output_path: str = "") -> str:
    """REMOVES duplicate rows. [ACTION]
    
    [RAG Context]
    Identifies and removes redundant rows to ensure data uniqueness.
    
    How to Use:
    - By default, looks at all columns.
    - Use 'subset' to check for duplicates based on specific identifiers (e.g., 'user_id' or 'email').
    
    Keywords: de-duplicate, unique rows, data cleaning, remove repeats.
    """
    from mcp_servers.pandas_server.tools import core_ops
    return core_ops.drop_duplicates(file_path, subset, output_path)

@mcp.tool()
def fill_na(file_path: str, value: Any, output_path: str, method: Optional[str] = None) -> str:
    """FILLS missing values (NaN). [ACTION]
    
    [RAG Context]
    Replaces null/missing entries with specific values or using statistical methods.
    
    How to Use:
    - Fill with a constant (e.g., replace missing scores with 0).
    - Use 'ffill' (Forward Fill) to propagate the last valid observation forward.
    - Use 'bfill' (Backward Fill) to propagate the next valid observation backward.
    
    Keywords: handle missing data, impute, null replacement, data completion.
    """
    from mcp_servers.pandas_server.tools import core_ops
    return core_ops.fill_na(file_path, value, output_path, method)

@mcp.tool()
def sample_data(file_path: str, n: Optional[int] = None, frac: Optional[float] = None, output_path: str = "") -> str:
    """SAMPLES random rows. [ACTION]
    
    [RAG Context]
    Randomly selects a subset of rows from the dataset. Use this when the dataset is too large for efficient processing or when you need a representative "slice" of the data for testing.
    
    How to Use:
    - Use 'n' to specify an exact number of rows (e.g., 100 rows).
    - Use 'frac' to specify a percentage (e.g., 0.1 for 10% of the total data).
    
    Keywords: random sample, subset data, data slice, test data.
    """
    from mcp_servers.pandas_server.tools import core_ops
    return core_ops.sample_data(file_path, n, frac, output_path)

@mcp.tool()
def astype(file_path: str, column_types: Dict[str, str], output_path: str) -> str:
    """CASTS column data types. [ACTION]
    
    [RAG Context]
    Explicitly changes the data type of one or more columns.
    
    How to Use:
    - Crucial for data cleaning when numeric columns are loaded as strings ('object').
    - Example mapping: `{"price": "float", "id": "int", "timestamp": "datetime"}`.
    
    Keywords: change type, cast column, data conversion, numeric conversion.
    """
    from mcp_servers.pandas_server.tools import core_ops
    return core_ops.astype(file_path, column_types, output_path)

@mcp.tool()
def rename_columns(file_path: str, mapping: Dict[str, str], output_path: str) -> str:
    """RENAMES columns. [ACTION]
    
    [RAG Context]
    Modifies the header names of the dataset.
    
    How to Use:
    - Use to standardize column names across different datasets.
    - Example: `{"old_col_1": "user_id", "Col2": "revenue"}`.
    
    Keywords: change header, rename field, column alias, data standardization.
    """
    from mcp_servers.pandas_server.tools import core_ops
    return core_ops.rename_columns(file_path, mapping, output_path)

@mcp.tool()
def set_index(file_path: str, columns: Union[str, List[str]], drop: bool = True, output_path: str = "") -> str:
    """SETS column as index. [ACTION]
    
    [RAG Context]
    Promotes one or more columns to become the "index" (row labels) of the dataset.
    
    How to Use:
    - Useful for time-series (setting 'date' as index) or unique identifier lookups (setting 'id' as index).
    - Helps in aligning data during joins or complex aggregations.
    
    Keywords: row index, primary key, data alignment, set labels.
    """
    from mcp_servers.pandas_server.tools import core_ops
    return core_ops.set_index(file_path, columns, drop, output_path)

@mcp.tool()
def reset_index(file_path: str, drop: bool = False, output_path: str = "") -> str:
    """RESETS index to integer sequence. [ACTION]
    
    [RAG Context]
    Converts the current index back into a regular column and replaces it with a simple 0, 1, 2... integer range.
    
    How to Use:
    - Use after merging or filtering to normalize the row numbers.
    - If 'drop' is True, the old index is discarded entirely.
    
    Keywords: normalize index, re-index, clear labels, sequential index.
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
    Performs the powerful Split-Apply-Combine pattern. It divides the dataset into groups based on specific columns and then calculates summary statistics for each group.
    
    How to Use:
    - Crucial for reporting (e.g., "Total sales by region", "Average user age by city").
    - 'agg' format: `{"sales": "sum", "age": ["mean", "max"]}`.
    - Result is saved to 'output_path'.
    
    Arguments:
    - by: Column names defining the groups.
    - agg: Dictionary mapping columns to aggregation functions ('sum', 'mean', 'count', 'min', 'max').
    
    Keywords: aggregation, summary report, group analytics, split apply combine.
    """
    from mcp_servers.pandas_server.tools import transform_ops
    return transform_ops.group_by(file_path, by, agg, output_path)

@mcp.tool()
def merge_datasets(left_path: str, right_path: str, on: Union[str, List[str]], how: str, output_path: str) -> str:
    """JOINS two datasets (SQL-style). [ACTION]
    
    [RAG Context]
    Combines two separate data files into one using a common key/column, identical to a SQL JOIN operation.
    
    How to Use:
    - Use 'inner' to keep only matching rows.
    - Use 'left' to keep all rows from the first file and matching rows from the second.
    - Use 'outer' to keep all rows from both files (filling unmatched with NaN).
    - Example: Merge 'users.csv' and 'orders.csv' on 'user_id'.
    
    Arguments:
    - left_path: Path to the first file.
    - right_path: Path to the second file.
    - on: The common key column(s).
    - how: 'inner', 'left', 'right', 'outer'.
    
    Keywords: relational join, data fusion, combine files, sql join, vlookup.
    """
    from mcp_servers.pandas_server.tools import transform_ops
    return transform_ops.merge_datasets(left_path, right_path, on, how, output_path)

@mcp.tool()
def concat_datasets(file_paths: List[str], axis: int, output_path: str) -> str:
    """COMBINES datasets vertically or horizontally. [ACTION]
    
    [RAG Context]
    Glues multiple datasets together along a specific axis.
    
    How to Use:
    - Vertical Stacking (axis=0): Useful for appending rows (e.g., merging 'sales_jan.csv' and 'sales_feb.csv').
    - Horizontal Stacking (axis=1): Useful for adding new features/columns from a file with the same row count.
    
    Arguments:
    - file_paths: List of absolute paths to the files.
    - axis: 0 for rows (vertical), 1 for columns (horizontal).
    
    Keywords: append data, stack datasets, bind rows, bind columns, merge vertical.
    """
    from mcp_servers.pandas_server.tools import transform_ops
    return transform_ops.concat_datasets(file_paths, axis, output_path)

@mcp.tool()
def pivot_table(file_path: str, values: str, index: Union[str, List[str]], columns: Union[str, List[str]], aggfunc: str, output_path: str) -> str:
    """RESHAPES data into a pivot table. [ACTION]
    
    [RAG Context]
    Creates a cross-tabulation summary by spreading unique values from one column into multiple headers.
    
    How to Use:
    - Essential for making "Wide" human-readable reports from "Long" technical data.
    - Example: `index="date", columns="category", values="revenue", aggfunc="sum"` creates a table where each row is a date and each column is a category showing its daily revenue.
    
    Arguments:
    - values: Metric to aggregate.
    - index: Column to use for row labels.
    - columns: Column to use for new headers.
    - aggfunc: e.g., 'mean', 'sum', 'count'.
    
    Keywords: spreadsheet pivot, crosstab, data reshaping, wide format, table summary.
    """
    from mcp_servers.pandas_server.tools import transform_ops
    return transform_ops.pivot_table(file_path, values, index, columns, aggfunc, output_path)

@mcp.tool()
def melt_data(file_path: str, id_vars: List[str], value_vars: Optional[List[str]], output_path: str) -> str:
    """UNPIVOTS wide data to long format. [ACTION]
    
    [RAG Context]
    Massages a "Wide" dataset into a "Long" format, making it Tidier and easier to process with other tools.
    
    How to Use:
    - Use when you have multiple columns representing the same variable (e.g., 'year_2020', 'year_2021', 'year_2022') and want to turn them into two columns: 'Year' and 'Value'.
    - Ideal for prepping data for visualization tools or time-series analysis.
    
    Keywords: tidy data, long format, unpivot, database prep, data normalization.
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
    Parses messy string or numeric date columns into standardized 'datetime64' objects. This is a mandatory step before any time-series analysis like resampling or rolling averages.
    
    How to Use:
    - Automatically handles most standard ISO formats.
    - If your dates are non-standard (e.g., "DD-MM-YYYY"), specify the 'format' using strftime codes (e.g., "%d-%m-%Y").
    
    Keywords: parse dates, timestamp conversion, datetime cast, format time.
    """
    from mcp_servers.pandas_server.tools import time_ops
    return time_ops.to_datetime(file_path, columns, output_path, format)

@mcp.tool()
def resample_data(file_path: str, rule: str, on: Optional[str] = None, agg: Dict[str, str] = None, output_path: str = "") -> str:
    """CHANGE time frequency (e.g. Daily -> Monthly). [ACTION]
    
    [RAG Context]
    Aggregates time-series data into a new bucket size. For example, converting high-frequency 1-minute data into daily summaries.
    
    How to Use:
    - 'rule' codes: 'D' (Day), 'W' (Week), 'M' (Month), 'H' (Hour), 'T' (Minute).
    - Provide 'agg' to define HOW to combine values (e.g., `{"price": "mean", "volume": "sum"}`).
    
    Arguments:
    - rule: Target frequency.
    - on: The datetime column to use (uses index if None).
    
    Keywords: downsample, frequency conversion, time bucket, data smoothing, ohlc transform.
    """
    from mcp_servers.pandas_server.tools import time_ops
    return time_ops.resample_data(file_path, rule, on=on, agg=agg, output_path=output_path)

@mcp.tool()
def rolling_window(file_path: str, window: int, agg: str, on: Optional[str] = None, columns: Optional[List[str]] = None, output_path: str = "") -> str:
    """CALCULATES moving averages/stats. [ACTION]
    
    [RAG Context]
    Computes a sliding window statistic. Most commonly used in finance for moving averages to smooth out short-term fluctuations and highlight long-term trends.
    
    How to Use:
    - 'window'=7 on a daily dataset produces a 7-day Moving Average (SMA).
    - 'agg' can be 'mean', 'sum', 'std', 'var', 'min', 'max'.
    
    Arguments:
    - window: Size of the window in number of observations.
    
    Keywords: simple moving average, SMA, sliding window, data trend, rolling mean.
    """
    from mcp_servers.pandas_server.tools import time_ops
    return time_ops.rolling_window(file_path, window, agg, on, columns, output_path)

@mcp.tool()
def shift_diff(file_path: str, periods: int, columns: List[str], operation: str, output_path: str) -> str:
    """SHIFTS or DIFFS data for lags/changes. [ACTION]
    
    [RAG Context]
    Calculates period-over-period differences or offsets data in time. 
    
    How to Use:
    - 'shift': Moves values forward or backward. Use periods=1 to get the previous value (lag), or periods=-1 to get the next value (lead).
    - 'diff': Calculates the absolute change from the previous period (Value_t - Value_t-1).
    
    Arguments:
    - periods: Number of steps to offset.
    - operation: 'shift' or 'diff'.
    
    Keywords: lag data, lead data, delta calculation, rate of change, time offset.
    """
    from mcp_servers.pandas_server.tools import time_ops
    return time_ops.shift_diff(file_path, periods, columns, operation, output_path)

@mcp.tool()
def dt_component(file_path: str, column: str, component: str, output_path: str) -> str:
    """EXTRACTS date parts (year, month, day). [ACTION]
    
    [RAG Context]
    Extracts high-level attributes from a datetime column to new features.
    
    How to Use:
    - Component types: 'year', 'month', 'day', 'hour', 'minute', 'second', 'microsecond', 'nanosecond', 'dayofweek', 'dayofyear', 'weekofyear', 'quarter', 'is_month_start', 'is_month_end'.
    - Crucial for time-based segmentation (e.g., "Analyze sales on weekends vs weekdays").
    
    Keywords: date parts, season analysis, weekday extractor, time features.
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
    Breaks apart a single text column into multiple columns or a list of elements based on a separator (e.g., a comma, space, or hyphen).
    
    How to Use:
    - Excellent for cleaning "FullName" into "FirstName" and "LastName".
    - 'pat': The separator string (e.g., `,`, `;`, `\|`).
    - 'expand': If True (default), returns a data file with new columns for each split part.
    
    Keywords: string tokenization, split column, text parser, delimiter, comma separated.
    """
    from mcp_servers.pandas_server.tools import text_ops
    return text_ops.str_split(file_path, column, pat, expand, output_path)

@mcp.tool()
def str_replace(file_path: str, column: str, pat: str, repl: str, regex: bool = False, output_path: str = "") -> str:
    """REPLACES pattern in string column. [ACTION]
    
    [RAG Context]
    Performs a search-and-replace operation on text data within a column.
    
    How to Use:
    - Use for mass corrections like fixing misspellings or removing currency symbols (e.g., replace "$" with "").
    - 'regex': Set to True to allow powerful Regular Expression pattern matching.
    
    Keywords: string replace, regex substitution, text correction, cleanup text.
    """
    from mcp_servers.pandas_server.tools import text_ops
    return text_ops.str_replace(file_path, column, pat, repl, regex, output_path)

@mcp.tool()
def str_extract(file_path: str, column: str, pat: str, output_path: str = "") -> str:
    """EXTRACTS regex groups from text. [ACTION]
    
    [RAG Context]
    Uses Regular Expressions (RegEx) to pull specific patterns out of a long string into new columns.
    
    How to Use:
    - Use capture groups `()` to define what to extract.
    - Example: Extracting email domains from full emails using `pat="@(.+)"`.
    
    Keywords: regex extraction, pattern matcher, text mining, pull groups.
    """
    from mcp_servers.pandas_server.tools import text_ops
    return text_ops.str_extract(file_path, column, pat, output_path)

@mcp.tool()
def str_case(file_path: str, column: str, case: str, output_path: str = "") -> str:
    """CONVERTS text case (lower/upper). [ACTION]
    
    [RAG Context]
    Standardizes the capitalization of a text column. 
    
    How to Use:
    - 'case' options:
        - 'lower': "hello world"
        - 'upper': "HELLO WORLD"
        - 'title': "Hello World"
        - 'capitalize': "Hello world"
    - Crucial for data normalization before performing merges or value_counts.
    
    Keywords: capitalization, lowercase transform, case sensitivity, text normalization.
    """
    from mcp_servers.pandas_server.tools import text_ops
    return text_ops.str_case(file_path, column, case, output_path)

@mcp.tool()
def str_contains(file_path: str, column: str, pat: str, regex: bool = False, output_path: str = "") -> str:
    """CHECKS if string contains pattern. [ACTION]
    
    [RAG Context]
    Creates a boolean (True/False) result based on whether a pattern exists within the text of each row.
    
    How to Use:
    - Often used for tagging or preliminary filtering (e.g., flag all rows containing the word "Error").
    
    Keywords: string search, keyword check, tag data, flag patterns.
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
    Formula: `(Value - Group_Mean) / Group_Std`. The Z-score tells you how many standard deviations a value is from the mean.
    
    How to Use:
    - Standard threshold is > 3 or < -3 for identifying statistical outliers.
    - Useful for error detection or finding anomalous data points (e.g., unusual transaction amounts).
    
    Keywords: zscore, outlier detection, data standardization, anomaly finder.
    """
    from mcp_servers.pandas_server.tools import stat_ops
    return stat_ops.calculate_zscore(file_path, columns, output_path)

@mcp.tool()
def rank_data(file_path: str, column: str, method: str = "average", ascending: bool = True, output_path: str = "") -> str:
    """ASSIGNS ranks to values. [ACTION]
    
    [RAG Context]
    Assigns a numerical rank to entries (1st, 2nd, etc.).
    
    How to Use:
    - 'method' options:
        - 'average': Default, ties receive the average of the ranks (e.g., 1, 2.5, 2.5, 4).
        - 'min': Lowest rank in the tie (1, 2, 2, 4).
        - 'max': Highest rank in the tie (1, 3, 3, 4).
        - 'dense': Like 'min' but next rank is +/-1 from previous (1, 2, 2, 3).
    - Useful for sports scoring, school grading, or identifying top performers.
    
    Keywords: ranking, leaderboard, dense rank, tie handling.
    """
    from mcp_servers.pandas_server.tools import stat_ops
    return stat_ops.rank_data(file_path, column, method, ascending, output_path)

@mcp.tool()
def quantile_stat(file_path: str, column: str, q: float) -> dict:
    """CALCULATES specific quantile. [DATA]
    
    [RAG Context]
    Returns the value at the specified quantile of a distribution.
    
    How to Use:
    - q=0.5: The Median.
    - q=0.25, 0.75: The lower and upper quartiles.
    - q=0.99: The 99th percentile (useful for SLA monitoring).
    
    Keywords: percentiles, quantiles, cut-off value, median.
    """
    from mcp_servers.pandas_server.tools import stat_ops
    return stat_ops.quantile(file_path, column, q)

@mcp.tool()
def correlation_matrix(file_path: str, method: str = "pearson") -> dict:
    """CALCULATES correlation matrix. [DATA]
    
    [RAG Context]
    Measures the strength and direction of the linear relationship between pairs of numeric columns.
    
    How to Use:
    - 1.0 = Perfect positive correlation.
    - -1.0 = Perfect negative correlation.
    - 0.0 = No linear relationship.
    - Helps in Feature Selection for ML models by identifying redundant variables.
    
    Keywords: pearson correlation, relationship strength, feature association, multicorelinearity.
    """
    from mcp_servers.pandas_server.tools import stat_ops
    return stat_ops.correlation_matrix(file_path, method)

@mcp.tool()
def clip_data(file_path: str, columns: List[str], lower: Optional[float] = None, upper: Optional[float] = None, output_path: str = "") -> str:
    """CLIPS values to specified bounds. [ACTION]
    
    [RAG Context]
    Force values to stay within a specific range. Any value below 'lower' is set to 'lower', and any value above 'upper' is set to 'upper'.
    
    How to Use:
    - Use for data normalization or to prevent Extreme Outliers from skewing ML models.
    - Example: Clip probability scores between [0.0, 1.0].
    
    Keywords: winsorizing, range clamping, bound values, outlier capping.
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
    Transforms a column where each cell contains a list or array into multiple rows, duplicating the other column values for each list element.
    
    How to Use:
    - Use for normalized data processing when a single row has multiple entries (e.g., 'tags' or 'categories' as a list).
    
    Keywords: list to rows, flatten array, unnest, data expansion.
    """
    from mcp_servers.pandas_server.tools import struct_ops
    return struct_ops.explode_list(file_path, column, output_path)

@mcp.tool()
def flatten_json(file_path: str, column: str, output_path: str, sep: str = "_") -> str:
    """FLATTENS nested JSON column. [ACTION]
    
    [RAG Context]
    Unpacks nested JSON objects inside a column into their own individual columns.
    
    How to Use:
    - Crucial for processing NoSQL-style exports or semi-structured API responses.
    - 'sep': String to use for naming the sub-columns (e.g., 'address_city', 'address_zip').
    
    Keywords: unpack json, nest removal, structure flattening, flat schema.
    """
    from mcp_servers.pandas_server.tools import struct_ops
    return struct_ops.flatten_json(file_path, column, output_path, sep)

@mcp.tool()
def stack_data(file_path: str, level: int = -1, output_path: str = "") -> str:
    """STACKS columns into index (Wide to Long). [ACTION]
    
    [RAG Context]
    Moves column labels into a new level of the Row Index. This is a technical variation of 'melt' that works directly with the MultiIndex.
    
    How to Use:
    - Helps in restructuring multi-level column headers into a hierarchical row index.
    - Opposite of 'unstack'.
    
    Keywords: pivot rows, multiindex stack, reshape technical.
    """
    from mcp_servers.pandas_server.tools import struct_ops
    return struct_ops.stack_unstack(file_path, 'stack', level, output_path)

@mcp.tool()
def unstack_data(file_path: str, level: int = -1, output_path: str = "") -> str:
    """UNSTACKS index into columns (Long to Wide). [ACTION]
    
    [RAG Context]
    The reverse of 'stack'. It takes a hierarchical row index and pivots one level into column headers.
    
    Keywords: pivot columns, unstack index, wide expansion.
    """
    from mcp_servers.pandas_server.tools import struct_ops
    return struct_ops.stack_unstack(file_path, 'unstack', level, output_path)

@mcp.tool()
def cross_join(left_path: str, right_path: str, output_path: str) -> str:
    """PERFORMS Cartesian product. [ACTION]
    
    [RAG Context]
    Creates a new dataset containing all possible combinations of rows from the two source files.
    
    How to Use:
    - Warning: Resulting row count is (LeftRows * RightRows). Use with caution on large files.
    - Useful for generating permutations (e.g., all combinations of 'Products' and 'Stores').
    
    Keywords: cartesian product, rows combination, permutation generator, cross product.
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
    Converts categorical variables into a series of binary (0 or 1) columns. This is a mandatory preprocessing step for most Machine Learning models (Linear Regression, SVMs) that cannot handle text labels directly.
    
    How to Use:
    - Each unique category in a column becomes a new column.
    - 'drop_first': Use to avoid the "Dummy Variable Trap" by removing one of the resulting columns (since it's linearly dependent on the others).
    
    Keywords: dummy variables, feature encoding, machine learning prep, categorical conversion.
    """
    from mcp_servers.pandas_server.tools import ml_ops
    return ml_ops.one_hot_encode(file_path, columns, output_path, drop_first)

@mcp.tool()
def bin_data(file_path: str, column: str, bins: Union[int, List[float]], labels: List[str] = None, method: str = 'cut', output_path: str = "") -> str:
    """BINS continuous data into intervals. [ACTION]
    
    [RAG Context]
    Discretizes continuous numerical data into discrete "bins" or groups.
    
    How to Use:
    - 'cut': Bins the data into equal-width buckets based on the values.
    - 'qcut': Bins the data into equal-sized buckets based on sample quantiles (each bin has roughly the same number of rows).
    - Example: Binning 'Age' (0-100) into 'Child', 'Adult', 'Senior'.
    
    Keywords: bucketing, discretization, grouping numbers, histogram prep.
    """
    from mcp_servers.pandas_server.tools import ml_ops
    return ml_ops.bin_data(file_path, column, bins, labels, method, output_path)

@mcp.tool()
def factorize_column(file_path: str, column: str, output_path: str) -> str:
    """ENCODES labels as integers. [ACTION]
    
    [RAG Context]
    Maps each unique category in a column to a unique integer starting from 0.
    
    How to Use:
    - Faster alternative to One-Hot encoding for tree-based models like Random Forest or XGBoost.
    - Preserves categorical information while satisfying the requirement for numeric inputs in ML.
    
    Keywords: label encoding, category mapping, ordinal encoding, integer conversion.
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
    Performs vector-based if-else logic across the entire dataset. It creates a new column (or replaces an existing one) based on a boolean condition.
    
    How to Use:
    - Example: `condition="age >= 18", value_if_true="Adult", value_if_false="Minor"`.
    - This is significantly faster and cleaner than writing custom Python loops.
    
    Keywords: if else logic, conditional column, data tagging, vectorized if.
    """
    from mcp_servers.pandas_server.tools import logic_ops
    return logic_ops.conditional_mask(file_path, condition, value_if_true, value_if_false, output_path, column)

@mcp.tool()
def isin_filter(file_path: str, column: str, values: List[Any], keep: bool = True, output_path: str = "") -> str:
    """FILTERS rows by list of values. [ACTION]
    
    [RAG Context]
    Retains or discards rows based on whether their values in a specific column match any item in a provided list. Equivalent to the SQL 'IN' clause.
    
    How to Use:
    - Example: Filter for products in categories `["Electronics", "Gadgets"]`.
    - Set 'keep=False' to perform a 'NOT IN' filter (exclusion).
    
    Keywords: list check, set membership, sql in, rows exclusion.
    """
    from mcp_servers.pandas_server.tools import logic_ops
    return logic_ops.isin_filter(file_path, column, values, keep, output_path)

@mcp.tool()
def compare_datasets(left_path: str, right_path: str) -> dict:
    """COMPARES two datasets for diffs. [DATA]
    
    [RAG Context]
    Performs a side-by-side comparison of two data files to identify additions, deletions, and value changes.
    
    How to Use:
    - Ideal for regression testing or tracking historical changes between two versions of the same dataset.
    
    Keywords: dataset diff, change log, version comparison, data parity.
    """
    from mcp_servers.pandas_server.tools import logic_ops
    return logic_ops.compare_datasets(left_path, right_path)

@mcp.tool()
def ewm_calc(file_path: str, span: float, agg: str, columns: List[str], output_path: str) -> str:
    """CALCULATES Exponential Weighted stats. [ACTION]
    
    [RAG Context]
    Computes moving statistics that give more weight to recent observations while "decaying" older ones.
    
    How to Use:
    - Exponential Moving Average (EMA) is a standard technical analysis tool for trend detection.
    - 'span': Represents the "decay" period (e.g., 20, 50).
    
    Keywords: ema, exponential smoothing, decay weighting, financial indicator.
    """
    from mcp_servers.pandas_server.tools import window_ops
    return window_ops.ewm_calc(file_path, span, agg, columns, output_path)

@mcp.tool()
def expanding_calc(file_path: str, agg: str, columns: List[str], output_path: str) -> str:
    """CALCULATES cumulative stats. [ACTION]
    
    [RAG Context]
    Calculates statistics that include ALL data from the beginning of the dataset up to the current row.
    
    How to Use:
    - Use for cumulative totals (Cumulative Sum) or expanding averages.
    - Result at row 'N' is the aggregation of rows 0 through N.
    
    Keywords: cumulative sum, running total, expanding average, growing window.
    """
    from mcp_servers.pandas_server.tools import window_ops
    return window_ops.expanding_calc(file_path, agg, columns, output_path)

@mcp.tool()
def pct_change(file_path: str, periods: int, columns: List[str], output_path: str) -> str:
    """CALCULATES percentage change over periods. [ACTION]
    
    [RAG Context]
    Computes the fraction change between the current and a prior element.
    
    How to Use:
    - Essential for calculating stock returns or growth rates.
    - Formula: `(Value_t - Value_t-n) / Value_t-n`.
    
    Keywords: percentage growth, returns, rate of change, relative difference.
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
    Applies standard NumPy/Pandas mathematical transformations to numerical columns.
    
    How to Use:
    - Common functions:
        - 'log': Natural logarithm (useful for handling skewed distributions).
        - 'exp': Exponential.
        - 'sqrt': Square root.
        - 'abs': Absolute value.
        - 'round': Nearest integer.
    
    Keywords: math transform, log scale, normalization, rounding, vectorized math.
    """
    from mcp_servers.pandas_server.tools import math_ops
    return math_ops.apply_math(file_path, columns, func, output_path)

@mcp.tool()
def normalize_minmax(file_path: str, columns: List[str], output_path: str) -> str:
    """SCALES data to [0, 1] range. [ACTION]
    
    [RAG Context]
    Linearly scales values so that the minimum value becomes 0 and the maximum value becomes 1. 
    
    How to Use:
    - Vital for Machine Learning algorithms like Neural Networks or K-Nearest Neighbors that are sensitive to the absolute scale of features.
    
    Keywords: minmax scaler, data scaling, 0-1 normalization, feature scaling.
    """
    from mcp_servers.pandas_server.tools import math_ops
    return math_ops.normalize_minmax(file_path, columns, output_path)

@mcp.tool()
def standardize_scale(file_path: str, columns: List[str], output_path: str) -> str:
    """SCALES data to Mean=0, Std=1. [ACTION]
    
    [RAG Context]
    Transforms values into Z-scores: `(x - mean) / std`. 
    
    How to Use:
    - This is the standard "StandardScaler" used in data science. It preserves the shape of the distribution while centering it around zero.
    
    Keywords: standard scaler, zscore scaling, statistics transform, centering data.
    """
    from mcp_servers.pandas_server.tools import math_ops
    return math_ops.standardize_scale(file_path, columns, output_path)

@mcp.tool()
def calc_stats_vector(file_path: str, columns: List[str], func: str) -> dict:
    """CALCULATES vector norms. [DATA]
    
    [RAG Context]
    Computes mathematical norms (L1, L2) for the specified columns.
    
    How to Use:
    - 'norm_l1': Sum of absolute values (Manhattan distance).
    - 'norm_l2': Square root of sum of squares (Euclidean distance).
    
    Keywords: vector norm, l1 norm, l2 norm, euclidean distance, magnitude.
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
    Automated check to ensure a dataset meets specific structural requirements. Prevents downstream tool failures by catching "Schema Drift" early.
    
    How to Use:
    - Pass 'required_columns' to ensure all mandatory features are present.
    - Optionally pass 'types' to verify that columns match expected types (e.g., 'id' is 'int64').
    
    Keywords: schema validation, data integrity, contract check, missing columns finder.
    """
    from mcp_servers.pandas_server.tools import quality_ops
    return quality_ops.validate_schema(file_path, required_columns, types)

@mcp.tool()
def check_constraints(file_path: str, constraints: List[str]) -> dict:
    """CHECKS data quality constraints. [DATA]
    
    [RAG Context]
    Runs high-level logical checks on the data values to identify anomalies or domain violations.
    
    How to Use:
    - Example constraints: `["age >= 0", "discount <= 1.0", "price > 0"]`.
    - Returns a summary of how many rows failed each check.
    
    Keywords: data audit, logical constraints, range check, domain validation.
    """
    from mcp_servers.pandas_server.tools import quality_ops
    return quality_ops.check_constraints(file_path, constraints)

@mcp.tool()
def drop_outliers(file_path: str, columns: List[str], factor: float = 1.5, output_path: str = "") -> str:
    """REMOVES outliers using IQR. [ACTION]
    
    [RAG Context]
    Automatically detects and deletes rows where the values in specific columns are numerically deviant (the interquartile range method).
    
    How to Use:
    - 'factor': Standard is 1.5. A higher factor (e.g., 3.0) is "less aggressive" and only removes extreme outliers (Tukey's fences).
    
    Keywords: remove outliers, iqr filter, data cleaning, statistically deviant rows.
    """
    from mcp_servers.pandas_server.tools import quality_ops
    return quality_ops.remove_outliers_iqr(file_path, columns, factor, output_path)

@mcp.tool()
def drop_empty_cols(file_path: str, threshold: float = 1.0, output_path: str = "") -> str:
    """DROPS columns with excessive NaNs. [ACTION]
    
    [RAG Context]
    Cleans up the dataset structure by removing columns that don't contain enough useful data.
    
    How to Use:
    - 'threshold': Percentage of Nulls allowed before dropping.
    - 1.0 = Only drop if ALL rows are empty.
    - 0.5 = Drop if more than 50% of the data is missing.
    
    Keywords: cleanup empty features, handle sparse data, drop null columns.
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
    Transforms raw strings into lists of words or sub-units (tokens), which is the first step in numerical representation for Natural Language Processing (NLP).
    
    How to Use:
    - Use before any statistical text analysis (e.g., word frequencies).
    - Returns a new file where the target column is converted to lists of tokens.
    
    Keywords: text tokenization, word splitting, nlp preprocessing, lexer.
    """
    from mcp_servers.pandas_server.tools import nlp_ops
    return nlp_ops.tokenize_text(file_path, column, output_path)

@mcp.tool()
def word_count(file_path: str, column: str, output_path: str) -> str:
    """COUNTS words and characters. [ACTION]
    
    [RAG Context]
    Extracts basic complexity metrics from text data.
    
    How to Use:
    - Calculated metrics: 'word_count', 'char_count', 'unique_word_count'.
    - Ideal for analyzing survey responses, social media messages, or long-form documents to gauge length and richness.
    
    Keywords: text length, document complexity, vocabulary size, character counter.
    """
    from mcp_servers.pandas_server.tools import nlp_ops
    return nlp_ops.count_words(file_path, column, output_path)

@mcp.tool()
def generate_ngrams(file_path: str, column: str, n: int, output_path: str) -> str:
    """GENERATES n-grams from text. [ACTION]
    
    [RAG Context]
    Produces sequences of 'n' consecutive items from given text.
    
    How to Use:
    - n=2 (Bigrams): e.g., "The quick", "quick brown".
    - n=3 (Trigrams): e.g., "The quick brown".
    - Helps in capturing context and phrases that single words (unigrams) miss.
    
    Keywords: bigrams, trigrams, phrase extraction, sequence mining.
    """
    from mcp_servers.pandas_server.tools import nlp_ops
    return nlp_ops.generate_ngrams(file_path, column, n, output_path)


# ==========================================
# 14. Feature Engineering (New)
# ==========================================
@mcp.tool()
def create_interactions(file_path: str, features: List[str], operations: List[str], output_path: str) -> str:
    """CREATES interaction features. [ACTION]
    
    [RAG Context]
    Automatically generates new feature columns by combining existing ones using basic arithmetic operations.
    
    How to Use:
    - Crucial for capturing synergy between variables (e.g., 'price' and 'quantity' to create 'revenue').
    - Operations: 'mul' (*), 'div' (/), 'add' (+), 'sub' (-).
    - If features are `[A, B]` and operations is `["mul"]`, a new column `A_mul_B` is created.
    
    Keywords: feature cross, synergy effects, derived features, formula creation.
    """
    from mcp_servers.pandas_server.tools import feature_ops
    return feature_ops.create_interactions(file_path, features, operations, output_path)

@mcp.tool()
def polynomial_features(file_path: str, columns: List[str], degree: int, output_path: str) -> str:
    """CREATES polynomial features. [ACTION]
    
    [RAG Context]
    Generates non-linear transformations (e.g., powers and interactions) of the input columns.
    
    How to Use:
    - degree=2 on `[x]` creates `[x, x^2]`.
    - Helps capture non-linear relationships in datasets that simple linear models might miss.
    
    Keywords: nonlinear features, power terms, polynomial expansion, higher degree features.
    """
    from mcp_servers.pandas_server.tools import feature_ops
    return feature_ops.polynomial_features(file_path, columns, degree, output_path)


# ==========================================
# 15. Chain Executor (Super Tool)
# ==========================================
@mcp.tool()
def execute_chain(initial_file_path: str, steps: List[Dict[str, Any]], final_output_path: Optional[str] = None) -> Dict[str, Any]:
    """EXECUTES a multi-step pipeline. [ACTION] (Advanced)
    
    [RAG Context]
    A "Super Tool" that runs a sequence of Pandas transformations in a single call, optimizing for multiple operations without intermediate file management overhead.
    
    How to Use:
    - Pass an 'initial_file_path' (e.g., 'raw_data.csv').
    - 'steps' is a list of objects defining the tool and its arguments.
    - Example: 
        ```json
        [
          {"tool": "filter_data", "args": {"query": "age > 20"}},
          {"tool": "rename_columns", "args": {"mapping": {"id": "user_id"}}}
        ]
        ```
    - Returns a summary of the operations performed and the final file location.
    
    Keywords: sequence executor, batch pipeline, automation chain, multi-op.
    """
    from mcp_servers.pandas_server.tools import chain_ops
    return chain_ops.execute_chain(initial_file_path, steps, final_output_path)


# ==========================================
# 16. Bulk Operations (New)
# ==========================================
@mcp.tool()
def bulk_read_datasets(urls: List[str]) -> Dict[str, Any]:
    """READS multiple datasets. [DATA]
    
    [RAG Context]
    Downloads and loads multiple datasets from URLs (CSV, JSON, ZIP).
    Returns a summary dictionary containing success/failure status and metadata.
    Supported formats: CSV, JSON, ZIP (containing CSVs).
    """
    from mcp_servers.pandas_server.tools import bulk_ops
    return bulk_ops.bulk_read_datasets(urls)

@mcp.tool()
def merge_datasets_bulk(file_paths: List[str], on: str, how: str = "inner", output_path: str = "") -> str:
    """MERGES multiple dataframes. [ACTION]
    
    [RAG Context]
    Iteratively merges a list of datasets on a common key.
    Useful for combining scattered data files into a master dataset.
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
    "Super Cleaner". Runs standard pipeline: 
    Headers, Whitespace, Empty Cols, Impute NaNs, Dates, Outliers.
    """
    from mcp_servers.pandas_server.tools import pipeline_ops
    return pipeline_ops.clean_dataset_auto(file_path, output_path)

@mcp.tool()
def generate_profile_report(file_path: str, output_path: str) -> str:
    """GENERATES HTML profile. [DATA]
    
    [RAG Context]
    Generates a comprehensive HTML report using ydata_profiling.
    Includes stats, correlations, distributions.
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

