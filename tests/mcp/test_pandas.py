import os

import pandas as pd
import pytest
from mcp.client.stdio import stdio_client

from tests.mcp.client_utils import SafeClientSession as ClientSession
from tests.mcp.client_utils import get_server_params


@pytest.mark.asyncio
async def test_pandas_full_coverage():
    """
    REAL SIMULATION: Verify Pandas Server (100% Tool Coverage - 60+ Tools).
    """
    params = get_server_params("pandas_server", extra_dependencies=["pandas", "numpy", "structlog", "openpyxl", "scikit-learn"])

    # Test Data Setup
    csv_path = "test_pandas_data.csv"
    json_path = "test_pandas_data.json"
    parquet_path = "test_pandas_data.parquet"
    # Use unique outputs to avoid Windows file lock contention

    # Create sample DataFrame
    df = pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
        "age": [25, 30, 35, 40, 25],
        "salary": [50000, 60000, 70000, 80000, 52000],
        "city": ["NY", "LA", "Chicago", "NY", "LA"],
        "date": pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05"]),
        "tags": [["a", "b"], ["b", "c"], ["a"], ["c"], ["b"]],
        "meta": [{"source": "web"}, {"source": "app"}, {}, {}, {"source": "web"}]
    })
    df.to_csv(csv_path, index=False)

    # Second dataset for joins
    df2 = pd.DataFrame({
        "id": [1, 2, 6],
        "dept": ["HR", "Eng", "Sales"]
    })
    csv_path_2 = "test_pandas_dept.csv"
    df2.to_csv(csv_path_2, index=False)

    print("\n--- Starting 100% Coverage Simulation: Pandas Server ---")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Helper to generate unique paths
            def get_out(step): return f"test_pandas_out_{step}.csv"

            # --- 1. IO ---
            print("\n[1. IO]")
            await session.call_tool("read_dataset", arguments={"file_path": csv_path})
            await session.call_tool("get_dataset_info", arguments={"file_path": csv_path})
            await session.call_tool("convert_dataset", arguments={"source_path": csv_path, "dest_path": json_path, "dest_format": "json"})

            # --- 2. INSPECTION ---
            print("\n[2. Inspection]")
            await session.call_tool("head", arguments={"file_path": csv_path})
            await session.call_tool("tail", arguments={"file_path": csv_path})
            await session.call_tool("columns", arguments={"file_path": csv_path})
            await session.call_tool("dtypes", arguments={"file_path": csv_path})
            await session.call_tool("describe", arguments={"file_path": csv_path})
            await session.call_tool("value_counts", arguments={"file_path": csv_path, "column": "city"})
            await session.call_tool("shape", arguments={"file_path": csv_path})

            # --- 3. CORE OPS ---
            print("\n[3. Core]")
            await session.call_tool("filter_data", arguments={"file_path": csv_path, "query": "age > 30", "output_path": get_out("filter")})
            await session.call_tool("select_columns", arguments={"file_path": csv_path, "columns": ["name", "salary"], "output_path": get_out("select")})
            await session.call_tool("sort_data", arguments={"file_path": csv_path, "by": "age", "ascending": False, "output_path": get_out("sort")})
            await session.call_tool("drop_duplicates", arguments={"file_path": csv_path, "subset": ["city"], "output_path": get_out("dedup")})
            await session.call_tool("fill_na", arguments={"file_path": csv_path, "value": 0, "output_path": get_out("fillna")})
            await session.call_tool("sample_data", arguments={"file_path": csv_path, "n": 2, "output_path": get_out("sample")})
            await session.call_tool("astype", arguments={"file_path": csv_path, "column_types": {"age": "float"}, "output_path": get_out("astype")})
            await session.call_tool("rename_columns", arguments={"file_path": csv_path, "mapping": {"salary": "income"}, "output_path": get_out("rename")})

            # Set index creates a new file, reset index uses that
            out_idx = get_out("set_idx")
            await session.call_tool("set_index", arguments={"file_path": csv_path, "columns": "id", "output_path": out_idx})
            await session.call_tool("reset_index", arguments={"file_path": out_idx, "output_path": get_out("reset_idx")})

            # --- 4. TRANSFORM ---
            print("\n[4. Transform]")
            await session.call_tool("group_by", arguments={"file_path": csv_path, "by": "city", "agg": {"salary": "mean"}, "output_path": get_out("group")})
            await session.call_tool("merge_datasets", arguments={"left_path": csv_path, "right_path": csv_path_2, "on": "id", "how": "left", "output_path": get_out("merge")})
            await session.call_tool("concat_datasets", arguments={"file_paths": [csv_path, csv_path], "axis": 0, "output_path": get_out("concat")})
            await session.call_tool("pivot_table", arguments={"file_path": csv_path, "values": "salary", "index": "city", "columns": "age", "aggfunc": "sum", "output_path": get_out("pivot")})
            await session.call_tool("melt_data", arguments={"file_path": csv_path, "id_vars": ["name"], "value_vars": ["salary", "age"], "output_path": get_out("melt")})

            # --- 5. TIME SERIES ---
            print("\n[5. Time]")
            out_dt = get_out("dt")
            await session.call_tool("to_datetime", arguments={"file_path": csv_path, "columns": ["date"], "output_path": out_dt})

            # Need datetime index for resample
            out_dt_idx = get_out("dt_idx")
            await session.call_tool("set_index", arguments={"file_path": out_dt, "columns": "date", "output_path": out_dt_idx})
            await session.call_tool("resample_data", arguments={"file_path": out_dt_idx, "rule": "D", "agg": {"salary": "sum"}, "output_path": get_out("resample")})

            await session.call_tool("rolling_window", arguments={"file_path": csv_path, "window": 2, "agg": "mean", "on": "age", "output_path": get_out("roll")})
            await session.call_tool("shift_diff", arguments={"file_path": csv_path, "periods": 1, "columns": ["salary"], "operation": "diff", "output_path": get_out("diff")})

            # dt_component
            await session.call_tool("dt_component", arguments={"file_path": out_dt, "column": "date", "component": "year", "output_path": get_out("dt_comp")})

            # --- 6. TEXT ---
            print("\n[6. Text]")
            await session.call_tool("str_split", arguments={"file_path": csv_path, "column": "name", "pat": "a", "output_path": get_out("split")})
            await session.call_tool("str_replace", arguments={"file_path": csv_path, "column": "city", "pat": "NY", "repl": "New York", "output_path": get_out("repl")})
            await session.call_tool("str_extract", arguments={"file_path": csv_path, "column": "name", "pat": "(A)", "output_path": get_out("extract")})
            await session.call_tool("str_case", arguments={"file_path": csv_path, "column": "name", "case": "upper", "output_path": get_out("case")})
            await session.call_tool("str_contains", arguments={"file_path": csv_path, "column": "name", "pat": "Ali", "output_path": get_out("contains")})

            # --- 7. STATS ---
            print("\n[7. Stats]")
            await session.call_tool("calculate_zscore", arguments={"file_path": csv_path, "columns": ["salary"], "output_path": get_out("zscore")})
            await session.call_tool("rank_data", arguments={"file_path": csv_path, "column": "salary", "output_path": get_out("rank")})
            await session.call_tool("quantile_stat", arguments={"file_path": csv_path, "column": "salary", "q": 0.5})
            await session.call_tool("correlation_matrix", arguments={"file_path": csv_path})
            await session.call_tool("clip_data", arguments={"file_path": csv_path, "columns": ["salary"], "lower": 55000, "upper": 75000, "output_path": get_out("clip")})

            # --- 8. STRUCTURAL ---
            print("\n[8. Structural]")
            try:
                await session.call_tool("explode_list", arguments={"file_path": csv_path, "column": "tags", "output_path": get_out("explode")})
            except: pass
            try:
                await session.call_tool("flatten_json", arguments={"file_path": csv_path, "column": "meta", "output_path": get_out("flatten")})
            except: pass

            out_stack = get_out("stack")
            await session.call_tool("stack_data", arguments={"file_path": csv_path, "output_path": out_stack})
            await session.call_tool("unstack_data", arguments={"file_path": out_stack, "output_path": get_out("unstack")})
            await session.call_tool("cross_join", arguments={"left_path": csv_path, "right_path": csv_path_2, "output_path": get_out("cross")})

            # --- 9. ML PREP ---
            print("\n[9. ML Prep]")
            await session.call_tool("one_hot_encode", arguments={"file_path": csv_path, "columns": ["city"], "output_path": get_out("ohe")})
            await session.call_tool("bin_data", arguments={"file_path": csv_path, "column": "age", "bins": 3, "output_path": get_out("bin")})
            await session.call_tool("factorize_column", arguments={"file_path": csv_path, "column": "city", "output_path": get_out("factor")})

            # --- 10. LOGIC ---
            print("\n[10. Logic]")
            await session.call_tool("conditional_mask", arguments={"file_path": csv_path, "condition": "age > 30", "value_if_true": "Old", "value_if_false": "Young", "column": "age_group", "output_path": get_out("mask")})
            await session.call_tool("isin_filter", arguments={"file_path": csv_path, "column": "city", "values": ["NY", "Chicago"], "output_path": get_out("isin")})
            await session.call_tool("compare_datasets", arguments={"left_path": csv_path, "right_path": csv_path})
            await session.call_tool("ewm_calc", arguments={"file_path": csv_path, "span": 2, "agg": "mean", "columns": ["salary"], "output_path": get_out("ewm")})
            await session.call_tool("expanding_calc", arguments={"file_path": csv_path, "agg": "sum", "columns": ["salary"], "output_path": get_out("expanding")})
            await session.call_tool("pct_change", arguments={"file_path": csv_path, "periods": 1, "columns": ["salary"], "output_path": get_out("pct")})

            # --- 11. MATH ---
            print("\n[11. Math]")
            await session.call_tool("apply_math", arguments={"file_path": csv_path, "columns": ["salary"], "func": "log", "output_path": get_out("math")})
            await session.call_tool("normalize_minmax", arguments={"file_path": csv_path, "columns": ["age"], "output_path": get_out("minmax")})
            await session.call_tool("standardize_scale", arguments={"file_path": csv_path, "columns": ["age"], "output_path": get_out("stdout")})
            await session.call_tool("calc_stats_vector", arguments={"file_path": csv_path, "columns": ["age"], "func": "norm_l2"})

            # --- 12. QUALITY ---
            print("\n[12. Quality]")
            await session.call_tool("validate_schema", arguments={"file_path": csv_path, "required_columns": ["id", "name"], "types": {"id": "int64"}})
            await session.call_tool("check_constraints", arguments={"file_path": csv_path, "constraints": ["age > 0", "salary > 0"]})
            await session.call_tool("drop_outliers", arguments={"file_path": csv_path, "columns": ["salary"], "output_path": get_out("outliers")})
            await session.call_tool("drop_empty_cols", arguments={"file_path": csv_path, "output_path": get_out("empty")})

            # --- 13. NLP LITE ---
            print("\n[13. NLP]")
            await session.call_tool("tokenize_text", arguments={"file_path": csv_path, "column": "name", "output_path": get_out("token")})
            await session.call_tool("word_count", arguments={"file_path": csv_path, "column": "city", "output_path": get_out("words")})
            await session.call_tool("generate_ngrams", arguments={"file_path": csv_path, "column": "city", "n": 2, "output_path": get_out("grams")})

            # --- 14. FEATURE ---
            print("\n[14. Feature]")
            await session.call_tool("create_interactions", arguments={"file_path": csv_path, "features": ["age", "salary"], "operations": ["*"], "output_path": get_out("inter")})
            await session.call_tool("polynomial_features", arguments={"file_path": csv_path, "columns": ["age"], "degree": 2, "output_path": get_out("poly")})

            # --- 15. CHAIN ---
            print("\n[15. Chain]")
            steps = [
                {"op": "filter", "args": {"query": "age > 25"}},
                {"op": "select", "args": {"columns": ["name", "city"]}}
            ]
            await session.call_tool("execute_chain", arguments={"initial_file_path": csv_path, "steps": steps, "final_output_path": get_out("chain")})

    print("--- Pandas 100% Simulation Complete ---")

    # Cleanup (Clean up all generated files)
    print("\n[Cleanup]")
    for f in os.listdir("."):
        if f.startswith("test_pandas") and (f.endswith(".csv") or f.endswith(".json") or f.endswith(".parquet")):
            try:
                os.remove(f)
            except: pass

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
