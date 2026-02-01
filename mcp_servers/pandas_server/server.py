
from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from tools import (
    io_ops, inspection_ops, core_ops, transform_ops, chain_ops, 
    time_ops, text_ops, stat_ops, struct_ops, ml_ops, logic_ops, 
    window_ops, math_ops, quality_ops, nlp_ops, feature_ops
)
import structlog
from typing import List, Union, Dict, Any, Optional

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("pandas_server")

# ==========================================
# 1. IO Operations
# ==========================================
@mcp.tool()
def read_dataset(file_path: str, format: str = None) -> dict:
    """Read dataset metadata and preview. Supports csv, excel, parquet, json, etc."""
    return io_ops.read_dataset(file_path, format=format)

@mcp.tool()
def convert_dataset(source_path: str, dest_path: str, source_format: str = None, dest_format: str = None) -> str:
    """Convert dataset format (e.g. csv -> parquet)."""
    return io_ops.convert_dataset(source_path, dest_path, source_format, dest_format)

@mcp.tool()
def get_dataset_info(file_path: str) -> dict:
    """Get detailed metadata (rows, cols, dtypes, memory)."""
    return io_ops.get_file_info(file_path)


# ==========================================
# 2. Inspection Operations
# ==========================================
@mcp.tool()
def head(file_path: str, n: int = 5) -> list:
    """Get first n rows."""
    return inspection_ops.inspect_head(file_path, n)

@mcp.tool()
def tail(file_path: str, n: int = 5) -> list:
    """Get last n rows."""
    return inspection_ops.inspect_tail(file_path, n)

@mcp.tool()
def columns(file_path: str) -> list:
    """Get column names."""
    return inspection_ops.inspect_columns(file_path)

@mcp.tool()
def dtypes(file_path: str) -> dict:
    """Get column data types."""
    return inspection_ops.inspect_dtypes(file_path)

@mcp.tool()
def describe(file_path: str) -> dict:
    """Get summary statistics."""
    return inspection_ops.inspect_describe(file_path)

@mcp.tool()
def value_counts(file_path: str, column: str, n: int = 10) -> dict:
    """Get value counts."""
    return inspection_ops.inspect_value_counts(file_path, column, n)

@mcp.tool()
def shape(file_path: str) -> tuple:
    """Get dimensions (rows, cols)."""
    return inspection_ops.inspect_shape(file_path)


# ==========================================
# 3. Core Operations
# ==========================================
@mcp.tool()
def filter_data(file_path: str, query: str, output_path: str) -> str:
    """Filter rows using SQL-like query (e.g. 'age > 25 and city == "NY"')."""
    return core_ops.filter_data(file_path, query, output_path)

@mcp.tool()
def select_columns(file_path: str, columns: List[str], output_path: str) -> str:
    """Select specific columns to keep."""
    return core_ops.select_columns(file_path, columns, output_path)

@mcp.tool()
def sort_data(file_path: str, by: Union[str, List[str]], ascending: bool, output_path: str) -> str:
    """Sort data by column(s)."""
    return core_ops.sort_data(file_path, by, ascending, output_path)

@mcp.tool()
def drop_duplicates(file_path: str, subset: Optional[List[str]] = None, output_path: str = "") -> str:
    """Drop duplicate rows."""
    return core_ops.drop_duplicates(file_path, subset, output_path)

@mcp.tool()
def fill_na(file_path: str, value: Any, output_path: str, method: Optional[str] = None) -> str:
    """Fill missing values with value or method ('ffill', 'bfill')."""
    return core_ops.fill_na(file_path, value, output_path, method)

@mcp.tool()
def sample_data(file_path: str, n: Optional[int] = None, frac: Optional[float] = None, output_path: str = "") -> str:
    """Sample random rows."""
    return core_ops.sample_data(file_path, n, frac, output_path)

@mcp.tool()
def astype(file_path: str, column_types: Dict[str, str], output_path: str) -> str:
    """Convert column types (e.g. {'age': 'int', 'price': 'float'})."""
    return core_ops.astype(file_path, column_types, output_path)

@mcp.tool()
def rename_columns(file_path: str, mapping: Dict[str, str], output_path: str) -> str:
    """Rename columns (e.g. {'old': 'new'})."""
    return core_ops.rename_columns(file_path, mapping, output_path)

@mcp.tool()
def set_index(file_path: str, columns: Union[str, List[str]], drop: bool = True, output_path: str = "") -> str:
    """Set one or more columns as the index."""
    return core_ops.set_index(file_path, columns, drop, output_path)

@mcp.tool()
def reset_index(file_path: str, drop: bool = False, output_path: str = "") -> str:
    """Reset index to standard sequential integers."""
    return core_ops.reset_index(file_path, drop, output_path)


# ==========================================
# 4. Transformation Operations
# ==========================================
@mcp.tool()
def group_by(file_path: str, by: Union[str, List[str]], agg: Dict[str, Union[str, List[str]]], output_path: str) -> str:
    """Group by and aggregate. agg={"col": "sum"} or {"col": ["min", "max"]}."""
    return transform_ops.group_by(file_path, by, agg, output_path)

@mcp.tool()
def merge_datasets(left_path: str, right_path: str, on: Union[str, List[str]], how: str, output_path: str) -> str:
    """Merge two datasets (SQL Join). how='inner', 'left', 'right', 'outer'."""
    return transform_ops.merge_datasets(left_path, right_path, on, how, output_path)

@mcp.tool()
def concat_datasets(file_paths: List[str], axis: int, output_path: str) -> str:
    """Concatenate datasets vertically (0) or horizontally (1)."""
    return transform_ops.concat_datasets(file_paths, axis, output_path)

@mcp.tool()
def pivot_table(file_path: str, values: str, index: Union[str, List[str]], columns: Union[str, List[str]], aggfunc: str, output_path: str) -> str:
    """Create a pivot table."""
    return transform_ops.pivot_table(file_path, values, index, columns, aggfunc, output_path)

@mcp.tool()
def melt_data(file_path: str, id_vars: List[str], value_vars: Optional[List[str]], output_path: str) -> str:
    """Unpivot DataFrame from wide to long format."""
    return transform_ops.melt_data(file_path, id_vars, value_vars, output_path)


# ==========================================
# 5. Time Series Operations
# ==========================================
@mcp.tool()
def to_datetime(file_path: str, columns: List[str], output_path: str, format: Optional[str] = None) -> str:
    """Convert columns to datetime format."""
    return time_ops.to_datetime(file_path, columns, output_path, format)

@mcp.tool()
def resample_data(file_path: str, rule: str, on: Optional[str] = None, agg: Dict[str, str] = None, output_path: str = "") -> str:
    """Resample time-series (e.g. 'D' to 'M'). rule='D' (day), 'H' (hour). agg={'col': 'sum'}."""
    return time_ops.resample_data(file_path, rule, on=on, agg=agg, output_path=output_path)

@mcp.tool()
def rolling_window(file_path: str, window: int, agg: str, on: Optional[str] = None, columns: Optional[List[str]] = None, output_path: str = "") -> str:
    """Apply rolling window (moving average/sum/std)."""
    return time_ops.rolling_window(file_path, window, agg, on, columns, output_path)

@mcp.tool()
def shift_diff(file_path: str, periods: int, columns: List[str], operation: str, output_path: str) -> str:
    """Shift (lag) or Diff (difference) data. operation='shift' or 'diff'."""
    return time_ops.shift_diff(file_path, periods, columns, operation, output_path)

@mcp.tool()
def dt_component(file_path: str, column: str, component: str, output_path: str) -> str:
    """Extract date component: 'year', 'month', 'day', 'hour', 'weekday'."""
    return time_ops.dt_accessor(file_path, column, component, output_path)


# ==========================================
# 6. Text Operations
# ==========================================
@mcp.tool()
def str_split(file_path: str, column: str, pat: Optional[str] = None, expand: bool = True, output_path: str = "") -> str:
    """Split string column by pattern."""
    return text_ops.str_split(file_path, column, pat, expand, output_path)

@mcp.tool()
def str_replace(file_path: str, column: str, pat: str, repl: str, regex: bool = False, output_path: str = "") -> str:
    """Replace pattern in string column."""
    return text_ops.str_replace(file_path, column, pat, repl, regex, output_path)

@mcp.tool()
def str_extract(file_path: str, column: str, pat: str, output_path: str = "") -> str:
    """Extract regex groups from string column."""
    return text_ops.str_extract(file_path, column, pat, output_path)

@mcp.tool()
def str_case(file_path: str, column: str, case: str, output_path: str = "") -> str:
    """Convert case: 'lower', 'upper', 'title'."""
    return text_ops.str_case(file_path, column, case, output_path)

@mcp.tool()
def str_contains(file_path: str, column: str, pat: str, regex: bool = False, output_path: str = "") -> str:
    """Check if string contains pattern (creates boolean mask)."""
    return text_ops.str_contains(file_path, column, pat, regex, output_path)


# ==========================================
# 7. Statistical Operations
# ==========================================
@mcp.tool()
def calculate_zscore(file_path: str, columns: List[str], output_path: str) -> str:
    """Calculate Z-Scores for outlier detection."""
    return stat_ops.calculate_zscore(file_path, columns, output_path)

@mcp.tool()
def rank_data(file_path: str, column: str, method: str = "average", ascending: bool = True, output_path: str = "") -> str:
    """Rank values in a column."""
    return stat_ops.rank_data(file_path, column, method, ascending, output_path)

@mcp.tool()
def quantile_stat(file_path: str, column: str, q: float) -> dict:
    """Calculate specific quantile value (e.g. 0.95)."""
    return stat_ops.quantile(file_path, column, q)

@mcp.tool()
def correlation_matrix(file_path: str, method: str = "pearson") -> dict:
    """Get correlation matrix."""
    return stat_ops.correlation_matrix(file_path, method)

@mcp.tool()
def clip_data(file_path: str, columns: List[str], lower: Optional[float] = None, upper: Optional[float] = None, output_path: str = "") -> str:
    """Clip values to specified bounds."""
    return stat_ops.clip_values(file_path, columns, lower, upper, output_path)


# ==========================================
# 8. Structural & Nested Data
# ==========================================
@mcp.tool()
def explode_list(file_path: str, column: str, output_path: str) -> str:
    """Explode list-like column into rows."""
    return struct_ops.explode_list(file_path, column, output_path)

@mcp.tool()
def flatten_json(file_path: str, column: str, output_path: str, sep: str = "_") -> str:
    """Flatten JSON column into separate columns."""
    return struct_ops.flatten_json(file_path, column, output_path, sep)

@mcp.tool()
def stack_data(file_path: str, level: int = -1, output_path: str = "") -> str:
    """Stack (reshape to long)."""
    return struct_ops.stack_unstack(file_path, 'stack', level, output_path)

@mcp.tool()
def unstack_data(file_path: str, level: int = -1, output_path: str = "") -> str:
    """Unstack (reshape to wide)."""
    return struct_ops.stack_unstack(file_path, 'unstack', level, output_path)

@mcp.tool()
def cross_join(left_path: str, right_path: str, output_path: str) -> str:
    """Cartesian product of two datasets."""
    return struct_ops.cross_join(left_path, right_path, output_path)


# ==========================================
# 9. ML Preprocessing
# ==========================================
@mcp.tool()
def one_hot_encode(file_path: str, columns: List[str], output_path: str, drop_first: bool = False) -> str:
    """One-hot encode categorical columns."""
    return ml_ops.one_hot_encode(file_path, columns, output_path, drop_first)

@mcp.tool()
def bin_data(file_path: str, column: str, bins: Union[int, List[float]], labels: List[str] = None, method: str = 'cut', output_path: str = "") -> str:
    """Bin continuous data (cut/qcut)."""
    return ml_ops.bin_data(file_path, column, bins, labels, method, output_path)

@mcp.tool()
def factorize_column(file_path: str, column: str, output_path: str) -> str:
    """Encode labels as integers."""
    return ml_ops.factorize_col(file_path, column, output_path)


# ==========================================
# 10. Logic & Windowing
# ==========================================
@mcp.tool()
def conditional_mask(file_path: str, condition: str, value_if_true: Any, value_if_false: Any, output_path: str, column: str) -> str:
    """Apply conditional logic to column (e.g. if age > 18, 'adult', 'child')."""
    return logic_ops.conditional_mask(file_path, condition, value_if_true, value_if_false, output_path, column)

@mcp.tool()
def isin_filter(file_path: str, column: str, values: List[Any], keep: bool = True, output_path: str = "") -> str:
    """Filter by list of values."""
    return logic_ops.isin_filter(file_path, column, values, keep, output_path)

@mcp.tool()
def compare_datasets(left_path: str, right_path: str) -> dict:
    """Compare two datasets and report differences."""
    return logic_ops.compare_datasets(left_path, right_path)

@mcp.tool()
def ewm_calc(file_path: str, span: float, agg: str, columns: List[str], output_path: str) -> str:
    """Calculate Exponential Weighted Moving stats."""
    return window_ops.ewm_calc(file_path, span, agg, columns, output_path)

@mcp.tool()
def expanding_calc(file_path: str, agg: str, columns: List[str], output_path: str) -> str:
    """Calculate expanding (cumulative) stats."""
    return window_ops.expanding_calc(file_path, agg, columns, output_path)

@mcp.tool()
def pct_change(file_path: str, periods: int, columns: List[str], output_path: str) -> str:
    """Calculate percentage change."""
    return window_ops.pct_change(file_path, periods, columns, output_path)


# ==========================================
# 11. Math & Scientific (New)
# ==========================================
@mcp.tool()
def apply_math(file_path: str, columns: List[str], func: str, output_path: str) -> str:
    """Apply math function (log, exp, sqrt, abs, round, floor, ceil)."""
    return math_ops.apply_math(file_path, columns, func, output_path)

@mcp.tool()
def normalize_minmax(file_path: str, columns: List[str], output_path: str) -> str:
    """Scale data to [0, 1]."""
    return math_ops.normalize_minmax(file_path, columns, output_path)

@mcp.tool()
def standardize_scale(file_path: str, columns: List[str], output_path: str) -> str:
    """Scale data to Mean=0, Std=1."""
    return math_ops.standardize_scale(file_path, columns, output_path)

@mcp.tool()
def calc_stats_vector(file_path: str, columns: List[str], func: str) -> dict:
    """Calculate vector norms (norm_l1, norm_l2)."""
    return math_ops.calc_stats_vector(file_path, columns, func)


# ==========================================
# 12. Quality & Validation (New)
# ==========================================
@mcp.tool()
def validate_schema(file_path: str, required_columns: List[str], types: Optional[Dict[str, str]] = None) -> dict:
    """Validate expected columns and types."""
    return quality_ops.validate_schema(file_path, required_columns, types)

@mcp.tool()
def check_constraints(file_path: str, constraints: List[str]) -> dict:
    """Check constraints like 'age > 0'. Returns violation counts."""
    return quality_ops.check_constraints(file_path, constraints)

@mcp.tool()
def drop_outliers(file_path: str, columns: List[str], factor: float = 1.5, output_path: str = "") -> str:
    """Remove outliers using IQR method."""
    return quality_ops.remove_outliers_iqr(file_path, columns, factor, output_path)

@mcp.tool()
def drop_empty_cols(file_path: str, threshold: float = 1.0, output_path: str = "") -> str:
    """Drop columns with > threshold fraction of NaNs."""
    return quality_ops.drop_empty_cols(file_path, threshold, output_path)


# ==========================================
# 13. NLP Lite (New)
# ==========================================
@mcp.tool()
def tokenize_text(file_path: str, column: str, output_path: str) -> str:
    """Tokenize text column into words."""
    return nlp_ops.tokenize_text(file_path, column, output_path)

@mcp.tool()
def word_count(file_path: str, column: str, output_path: str) -> str:
    """Count words and characters."""
    return nlp_ops.count_words(file_path, column, output_path)

@mcp.tool()
def generate_ngrams(file_path: str, column: str, n: int, output_path: str) -> str:
    """Generate n-grams (bigrams etc)."""
    return nlp_ops.generate_ngrams(file_path, column, n, output_path)


# ==========================================
# 14. Feature Engineering (New)
# ==========================================
@mcp.tool()
def create_interactions(file_path: str, features: List[str], operations: List[str], output_path: str) -> str:
    """Create interaction features (A*B, A/B)."""
    return feature_ops.create_interactions(file_path, features, operations, output_path)

@mcp.tool()
def polynomial_features(file_path: str, columns: List[str], degree: int, output_path: str) -> str:
    """Create polynomial features (x^2, x^3)."""
    return feature_ops.polynomial_features(file_path, columns, degree, output_path)


# ==========================================
# 15. Chain Executor (Super Tool)
# ==========================================
@mcp.tool()
def execute_chain(initial_file_path: str, steps: List[Dict[str, Any]], final_output_path: Optional[str] = None) -> Dict[str, Any]:
    """Execute a pipeline of ANY available pandas tool."""
    return chain_ops.execute_chain(initial_file_path, steps, final_output_path)

if __name__ == "__main__":
    mcp.run()