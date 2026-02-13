
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
from shared.logging import setup_logging
setup_logging()

mcp = FastMCP("pandas_server")

# ==========================================
# 1. IO Operations
# ==========================================
@mcp.tool()
def read_dataset(file_path: str, format: str = None) -> dict:
    """READS dataset metadata and preview. [ENTRY]
    
    [RAG Context]
    Universal reader (CSV, Excel, Parquet, JSON).
    Returns columns, types, and first 5 rows.
    """
    from mcp_servers.pandas_server.tools import io_ops
    return io_ops.read_dataset(file_path, format=format)

@mcp.tool()
def convert_dataset(source_path: str, dest_path: str, source_format: str = None, dest_format: str = None) -> str:
    """CONVERTS dataset file format. [ACTION]
    
    [RAG Context]
    Example: CSV to Parquet for performance.
    """
    from mcp_servers.pandas_server.tools import io_ops
    return io_ops.convert_dataset(source_path, dest_path, source_format, dest_format)

@mcp.tool()
def get_dataset_info(file_path: str) -> dict:
    """GETS detailed dataset metadata. [DATA]
    
    [RAG Context]
    Returns row count, column types, memory usage.
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
    Quick preview of data start.
    """
    from mcp_servers.pandas_server.tools import inspection_ops
    return inspection_ops.inspect_head(file_path, n)

@mcp.tool()
def tail(file_path: str, n: int = 5) -> list:
    """GETS last n rows of dataset. [DATA]
    
    [RAG Context]
    Quick preview of data end.
    """
    from mcp_servers.pandas_server.tools import inspection_ops
    return inspection_ops.inspect_tail(file_path, n)

@mcp.tool()
def columns(file_path: str) -> list:
    """GETS list of column names. [DATA]
    
    [RAG Context]
    Useful for checking schema.
    """
    from mcp_servers.pandas_server.tools import inspection_ops
    return inspection_ops.inspect_columns(file_path)

@mcp.tool()
def dtypes(file_path: str) -> dict:
    """GETS column data types. [DATA]
    
    [RAG Context]
    Returns mapping of column -> type (int64, float, object).
    """
    from mcp_servers.pandas_server.tools import inspection_ops
    return inspection_ops.inspect_dtypes(file_path)

@mcp.tool()
def describe(file_path: str) -> dict:
    """CALCULATES summary statistics. [DATA]
    
    [RAG Context]
    Mean, std, min, max, quartiles for numeric columns.
    """
    from mcp_servers.pandas_server.tools import inspection_ops
    return inspection_ops.inspect_describe(file_path)

@mcp.tool()
def value_counts(file_path: str, column: str, n: int = 10) -> dict:
    """COUNTS unique values in a column. [DATA]
    
    [RAG Context]
    Histogram-like frequency count for categorical data.
    """
    from mcp_servers.pandas_server.tools import inspection_ops
    return inspection_ops.inspect_value_counts(file_path, column, n)

@mcp.tool()
def shape(file_path: str) -> tuple:
    """GETS dataset dimensions (rows, cols). [DATA]
    
    [RAG Context]
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
    Syntax: 'age > 25 and city == "NY"'.
    Saves result to output_path.
    """
    from mcp_servers.pandas_server.tools import core_ops
    return core_ops.filter_data(file_path, query, output_path)

@mcp.tool()
def select_columns(file_path: str, columns: List[str], output_path: str) -> str:
    """KEEPS only specified columns. [ACTION]
    
    [RAG Context]
    Subsets dataset vertically.
    """
    from mcp_servers.pandas_server.tools import core_ops
    return core_ops.select_columns(file_path, columns, output_path)

@mcp.tool()
def sort_data(file_path: str, by: Union[str, List[str]], ascending: bool, output_path: str) -> str:
    """SORTS dataset by column(s). [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.pandas_server.tools import core_ops
    return core_ops.sort_data(file_path, by, ascending, output_path)

@mcp.tool()
def drop_duplicates(file_path: str, subset: Optional[List[str]] = None, output_path: str = "") -> str:
    """REMOVES duplicate rows. [ACTION]
    
    [RAG Context]
    Args:
        subset: Columns to consider for identifying duplicates.
    """
    from mcp_servers.pandas_server.tools import core_ops
    return core_ops.drop_duplicates(file_path, subset, output_path)

@mcp.tool()
def fill_na(file_path: str, value: Any, output_path: str, method: Optional[str] = None) -> str:
    """FILLS missing values (NaN). [ACTION]
    
    [RAG Context]
    Args:
        value: Static value to fill (e.g. 0).
        method: 'ffill' (forward) or 'bfill' (backward).
    """
    from mcp_servers.pandas_server.tools import core_ops
    return core_ops.fill_na(file_path, value, output_path, method)

@mcp.tool()
def sample_data(file_path: str, n: Optional[int] = None, frac: Optional[float] = None, output_path: str = "") -> str:
    """SAMPLES random rows. [ACTION]
    
    [RAG Context]
    Args:
        n: Number of rows.
        frac: Fraction of rows (0.1 = 10%).
    """
    from mcp_servers.pandas_server.tools import core_ops
    return core_ops.sample_data(file_path, n, frac, output_path)

@mcp.tool()
def astype(file_path: str, column_types: Dict[str, str], output_path: str) -> str:
    """CASTS column data types. [ACTION]
    
    [RAG Context]
    Example: {'price': 'float', 'id': 'str'}.
    """
    from mcp_servers.pandas_server.tools import core_ops
    return core_ops.astype(file_path, column_types, output_path)

@mcp.tool()
def rename_columns(file_path: str, mapping: Dict[str, str], output_path: str) -> str:
    """RENAMES columns. [ACTION]
    
    [RAG Context]
    Example: {'old_name': 'new_name'}.
    """
    from mcp_servers.pandas_server.tools import core_ops
    return core_ops.rename_columns(file_path, mapping, output_path)

@mcp.tool()
def set_index(file_path: str, columns: Union[str, List[str]], drop: bool = True, output_path: str = "") -> str:
    """SETS column as index. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.pandas_server.tools import core_ops
    return core_ops.set_index(file_path, columns, drop, output_path)

@mcp.tool()
def reset_index(file_path: str, drop: bool = False, output_path: str = "") -> str:
    """RESETS index to integer sequence. [ACTION]
    
    [RAG Context]
    Moves current index into a column.
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
    Example: agg={"salary": "mean", "age": ["min", "max"]}.
    """
    from mcp_servers.pandas_server.tools import transform_ops
    return transform_ops.group_by(file_path, by, agg, output_path)

@mcp.tool()
def merge_datasets(left_path: str, right_path: str, on: Union[str, List[str]], how: str, output_path: str) -> str:
    """JOINS two datasets (SQL-style). [ACTION]
    
    [RAG Context]
    Args:
        how: 'inner', 'left', 'right', 'outer'.
    """
    from mcp_servers.pandas_server.tools import transform_ops
    return transform_ops.merge_datasets(left_path, right_path, on, how, output_path)

@mcp.tool()
def concat_datasets(file_paths: List[str], axis: int, output_path: str) -> str:
    """COMBINES datasets vertically or horizontally. [ACTION]
    
    [RAG Context]
    Args:
        axis: 0 (vertical/stack), 1 (horizontal/wide).
    """
    from mcp_servers.pandas_server.tools import transform_ops
    return transform_ops.concat_datasets(file_paths, axis, output_path)

@mcp.tool()
def pivot_table(file_path: str, values: str, index: Union[str, List[str]], columns: Union[str, List[str]], aggfunc: str, output_path: str) -> str:
    """RESHAPES data into a pivot table. [ACTION]
    
    [RAG Context]
    spreads rows into columns.
    """
    from mcp_servers.pandas_server.tools import transform_ops
    return transform_ops.pivot_table(file_path, values, index, columns, aggfunc, output_path)

@mcp.tool()
def melt_data(file_path: str, id_vars: List[str], value_vars: Optional[List[str]], output_path: str) -> str:
    """UNPIVOTS wide data to long format. [ACTION]
    
    [RAG Context]
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
    Essential for time-series analysis.
    """
    from mcp_servers.pandas_server.tools import time_ops
    return time_ops.to_datetime(file_path, columns, output_path, format)

@mcp.tool()
def resample_data(file_path: str, rule: str, on: Optional[str] = None, agg: Dict[str, str] = None, output_path: str = "") -> str:
    """CHANGE time frequency (e.g. Daily -> Monthly). [ACTION]
    
    [RAG Context]
    Args:
        rule: 'D', 'W', 'M', 'H', 'T' (min).
        agg: Aggregation method (e.g. {"price": "mean"}).
    """
    from mcp_servers.pandas_server.tools import time_ops
    return time_ops.resample_data(file_path, rule, on=on, agg=agg, output_path=output_path)

@mcp.tool()
def rolling_window(file_path: str, window: int, agg: str, on: Optional[str] = None, columns: Optional[List[str]] = None, output_path: str = "") -> str:
    """CALCULATES moving averages/stats. [ACTION]
    
    [RAG Context]
    Args:
        window: Size of window (e.g. 7 for 7-day moving avg).
        agg: "mean", "sum", "std".
    """
    from mcp_servers.pandas_server.tools import time_ops
    return time_ops.rolling_window(file_path, window, agg, on, columns, output_path)

@mcp.tool()
def shift_diff(file_path: str, periods: int, columns: List[str], operation: str, output_path: str) -> str:
    """SHIFTS or DIFFS data for lags/changes. [ACTION]
    
    [RAG Context]
    Args:
        operation: 'shift' (lead/lag) or 'diff' (delta).
    """
    from mcp_servers.pandas_server.tools import time_ops
    return time_ops.shift_diff(file_path, periods, columns, operation, output_path)

@mcp.tool()
def dt_component(file_path: str, column: str, component: str, output_path: str) -> str:
    """EXTRACTS date parts (year, month, day). [ACTION]
    
    [RAG Context]
    Args:
        component: 'year', 'month', 'day', 'hour', 'weekday'.
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
    """
    from mcp_servers.pandas_server.tools import text_ops
    return text_ops.str_split(file_path, column, pat, expand, output_path)

@mcp.tool()
def str_replace(file_path: str, column: str, pat: str, repl: str, regex: bool = False, output_path: str = "") -> str:
    """REPLACES pattern in string column. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.pandas_server.tools import text_ops
    return text_ops.str_replace(file_path, column, pat, repl, regex, output_path)

@mcp.tool()
def str_extract(file_path: str, column: str, pat: str, output_path: str = "") -> str:
    """EXTRACTS regex groups from text. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.pandas_server.tools import text_ops
    return text_ops.str_extract(file_path, column, pat, output_path)

@mcp.tool()
def str_case(file_path: str, column: str, case: str, output_path: str = "") -> str:
    """CONVERTS text case (lower/upper). [ACTION]
    
    [RAG Context]
    Args:
        case: 'lower', 'upper', 'title'.
    """
    from mcp_servers.pandas_server.tools import text_ops
    return text_ops.str_case(file_path, column, case, output_path)

@mcp.tool()
def str_contains(file_path: str, column: str, pat: str, regex: bool = False, output_path: str = "") -> str:
    """CHECKS if string contains pattern. [ACTION]
    
    [RAG Context]
    Creates boolean mask.
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
    (Value - Mean) / Std.
    """
    from mcp_servers.pandas_server.tools import stat_ops
    return stat_ops.calculate_zscore(file_path, columns, output_path)

@mcp.tool()
def rank_data(file_path: str, column: str, method: str = "average", ascending: bool = True, output_path: str = "") -> str:
    """ASSIGNS ranks to values. [ACTION]
    
    [RAG Context]
    Args:
        method: 'average', 'min', 'max', 'first', 'dense'.
    """
    from mcp_servers.pandas_server.tools import stat_ops
    return stat_ops.rank_data(file_path, column, method, ascending, output_path)

@mcp.tool()
def quantile_stat(file_path: str, column: str, q: float) -> dict:
    """CALCULATES specific quantile. [DATA]
    
    [RAG Context]
    Args:
        q: 0.5 (median), 0.95 (95th percentile).
    """
    from mcp_servers.pandas_server.tools import stat_ops
    return stat_ops.quantile(file_path, column, q)

@mcp.tool()
def correlation_matrix(file_path: str, method: str = "pearson") -> dict:
    """CALCULATES correlation matrix. [DATA]
    
    [RAG Context]
    Args:
        method: 'pearson', 'kendall', 'spearman'.
    """
    from mcp_servers.pandas_server.tools import stat_ops
    return stat_ops.correlation_matrix(file_path, method)

@mcp.tool()
def clip_data(file_path: str, columns: List[str], lower: Optional[float] = None, upper: Optional[float] = None, output_path: str = "") -> str:
    """CLIPS values to specified bounds. [ACTION]
    
    [RAG Context]
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
    One row per list element.
    """
    from mcp_servers.pandas_server.tools import struct_ops
    return struct_ops.explode_list(file_path, column, output_path)

@mcp.tool()
def flatten_json(file_path: str, column: str, output_path: str, sep: str = "_") -> str:
    """FLATTENS nested JSON column. [ACTION]
    
    [RAG Context]
    Converts keys to columns.
    """
    from mcp_servers.pandas_server.tools import struct_ops
    return struct_ops.flatten_json(file_path, column, output_path, sep)

@mcp.tool()
def stack_data(file_path: str, level: int = -1, output_path: str = "") -> str:
    """STACKS columns into index (Wide to Long). [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.pandas_server.tools import struct_ops
    return struct_ops.stack_unstack(file_path, 'stack', level, output_path)

@mcp.tool()
def unstack_data(file_path: str, level: int = -1, output_path: str = "") -> str:
    """UNSTACKS index into columns (Long to Wide). [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.pandas_server.tools import struct_ops
    return struct_ops.stack_unstack(file_path, 'unstack', level, output_path)

@mcp.tool()
def cross_join(left_path: str, right_path: str, output_path: str) -> str:
    """PERFORMS Cartesian product. [ACTION]
    
    [RAG Context]
    All combinations of rows.
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
    Creates dummy variables.
    """
    from mcp_servers.pandas_server.tools import ml_ops
    return ml_ops.one_hot_encode(file_path, columns, output_path, drop_first)

@mcp.tool()
def bin_data(file_path: str, column: str, bins: Union[int, List[float]], labels: List[str] = None, method: str = 'cut', output_path: str = "") -> str:
    """BINS continuous data into intervals. [ACTION]
    
    [RAG Context]
    Args:
        method: 'cut' (fixed width) or 'qcut' (quantile).
    """
    from mcp_servers.pandas_server.tools import ml_ops
    return ml_ops.bin_data(file_path, column, bins, labels, method, output_path)

@mcp.tool()
def factorize_column(file_path: str, column: str, output_path: str) -> str:
    """ENCODES labels as integers. [ACTION]
    
    [RAG Context]
    Simple label encoding.
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
    Example: if age > 18, 'adult', 'child'.
    """
    from mcp_servers.pandas_server.tools import logic_ops
    return logic_ops.conditional_mask(file_path, condition, value_if_true, value_if_false, output_path, column)

@mcp.tool()
def isin_filter(file_path: str, column: str, values: List[Any], keep: bool = True, output_path: str = "") -> str:
    """FILTERS rows by list of values. [ACTION]
    
    [RAG Context]
    SQL IN clause equivalent.
    """
    from mcp_servers.pandas_server.tools import logic_ops
    return logic_ops.isin_filter(file_path, column, values, keep, output_path)

@mcp.tool()
def compare_datasets(left_path: str, right_path: str) -> dict:
    """COMPARES two datasets for diffs. [DATA]
    
    [RAG Context]
    Returns rows present in one but not the other.
    """
    from mcp_servers.pandas_server.tools import logic_ops
    return logic_ops.compare_datasets(left_path, right_path)

@mcp.tool()
def ewm_calc(file_path: str, span: float, agg: str, columns: List[str], output_path: str) -> str:
    """CALCULATES Exponential Weighted stats. [ACTION]
    
    [RAG Context]
    Args:
        span: Decay parameter.
        agg: 'mean', 'std', 'var'.
    """
    from mcp_servers.pandas_server.tools import window_ops
    return window_ops.ewm_calc(file_path, span, agg, columns, output_path)

@mcp.tool()
def expanding_calc(file_path: str, agg: str, columns: List[str], output_path: str) -> str:
    """CALCULATES cumulative stats. [ACTION]
    
    [RAG Context]
    Expanding window (1 to N).
    """
    from mcp_servers.pandas_server.tools import window_ops
    return window_ops.expanding_calc(file_path, agg, columns, output_path)

@mcp.tool()
def pct_change(file_path: str, periods: int, columns: List[str], output_path: str) -> str:
    """CALCULATES percentage change over periods. [ACTION]
    
    [RAG Context]
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
    Args:
        func: 'log', 'exp', 'sqrt', 'abs', 'round', 'floor', 'ceil'.
    """
    from mcp_servers.pandas_server.tools import math_ops
    return math_ops.apply_math(file_path, columns, func, output_path)

@mcp.tool()
def normalize_minmax(file_path: str, columns: List[str], output_path: str) -> str:
    """SCALES data to [0, 1] range. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.pandas_server.tools import math_ops
    return math_ops.normalize_minmax(file_path, columns, output_path)

@mcp.tool()
def standardize_scale(file_path: str, columns: List[str], output_path: str) -> str:
    """SCALES data to Mean=0, Std=1. [ACTION]
    
    [RAG Context]
    Z-score normalization.
    """
    from mcp_servers.pandas_server.tools import math_ops
    return math_ops.standardize_scale(file_path, columns, output_path)

@mcp.tool()
def calc_stats_vector(file_path: str, columns: List[str], func: str) -> dict:
    """CALCULATES vector norms. [DATA]
    
    [RAG Context]
    Args:
        func: 'norm_l1', 'norm_l2'.
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
    Checks for missing columns and type mismatches.
    """
    from mcp_servers.pandas_server.tools import quality_ops
    return quality_ops.validate_schema(file_path, required_columns, types)

@mcp.tool()
def check_constraints(file_path: str, constraints: List[str]) -> dict:
    """CHECKS data quality constraints. [DATA]
    
    [RAG Context]
    Example: 'age > 0'. Returns failure counts.
    """
    from mcp_servers.pandas_server.tools import quality_ops
    return quality_ops.check_constraints(file_path, constraints)

@mcp.tool()
def drop_outliers(file_path: str, columns: List[str], factor: float = 1.5, output_path: str = "") -> str:
    """REMOVES outliers using IQR. [ACTION]
    
    [RAG Context]
    Args:
        factor: IQR multiplier (default 1.5).
    """
    from mcp_servers.pandas_server.tools import quality_ops
    return quality_ops.remove_outliers_iqr(file_path, columns, factor, output_path)

@mcp.tool()
def drop_empty_cols(file_path: str, threshold: float = 1.0, output_path: str = "") -> str:
    """DROPS columns with excessive NaNs. [ACTION]
    
    [RAG Context]
    Args:
        threshold: 1.0 = drop if ALL empty.
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
    Splits text into words/tokens.
    """
    from mcp_servers.pandas_server.tools import nlp_ops
    return nlp_ops.tokenize_text(file_path, column, output_path)

@mcp.tool()
def word_count(file_path: str, column: str, output_path: str) -> str:
    """COUNTS words and characters. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.pandas_server.tools import nlp_ops
    return nlp_ops.count_words(file_path, column, output_path)

@mcp.tool()
def generate_ngrams(file_path: str, column: str, n: int, output_path: str) -> str:
    """GENERATES n-grams from text. [ACTION]
    
    [RAG Context]
    Args:
        n: 2 (bigrams), 3 (trigrams).
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
    Example: A*B, A/B.
    """
    from mcp_servers.pandas_server.tools import feature_ops
    return feature_ops.create_interactions(file_path, features, operations, output_path)

@mcp.tool()
def polynomial_features(file_path: str, columns: List[str], degree: int, output_path: str) -> str:
    """CREATES polynomial features. [ACTION]
    
    [RAG Context]
    Example: x^2, x^3.
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
    Runs multiple pandas tools in sequence.
    Example: steps=[{"tool": "filter_data", "args": {...}}, ...]
    """
    from mcp_servers.pandas_server.tools import chain_ops
    return chain_ops.execute_chain(initial_file_path, steps, final_output_path)

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
