import os
import uuid
import structlog
from typing import List, Dict, Any, Optional
from mcp_servers.pandas_server.tools import (
    core_ops, transform_ops, io_ops, time_ops, text_ops, stat_ops, 
    struct_ops, ml_ops, logic_ops, window_ops, math_ops, quality_ops, nlp_ops, feature_ops
)

logger = structlog.get_logger()

# Mapping of operation names to their functions
# To allow string references in the chain
OP_MAP = {
    # Core
    'filter': core_ops.filter_data,
    'select': core_ops.select_columns,
    'sort': core_ops.sort_data,
    'drop_duplicates': core_ops.drop_duplicates,
    'fillna': core_ops.fill_na,
    'sample': core_ops.sample_data,
    'astype': core_ops.astype,
    'rename': core_ops.rename_columns,
    'set_index': core_ops.set_index,
    'reset_index': core_ops.reset_index,
    
    # Transform
    'group_by': transform_ops.group_by,
    'merge': transform_ops.merge_datasets,
    'concat': transform_ops.concat_datasets,
    'pivot': transform_ops.pivot_table,
    'melt': transform_ops.melt_data,
    
    # Structure
    'explode': struct_ops.explode_list,
    'flatten_json': struct_ops.flatten_json,
    'stack': lambda **k: struct_ops.stack_unstack(operation='stack', **k),
    'unstack': lambda **k: struct_ops.stack_unstack(operation='unstack', **k),
    'cross_join': struct_ops.cross_join,

    # ML
    'one_hot': ml_ops.one_hot_encode,
    'bin': ml_ops.bin_data,
    'factorize': ml_ops.factorize_col,

    # Logic
    'mask': logic_ops.conditional_mask,
    'isin': logic_ops.isin_filter,

    # Window
    'ewm': window_ops.ewm_calc,
    'expanding': window_ops.expanding_calc,
    'pct_change': window_ops.pct_change,

    # Time
    'to_datetime': time_ops.to_datetime,
    'resample': time_ops.resample_data,
    'rolling': time_ops.rolling_window,
    'shift_diff': time_ops.shift_diff,
    'dt_part': time_ops.dt_accessor,
    
    # Text
    'str_split': text_ops.str_split,
    'str_replace': text_ops.str_replace,
    'str_extract': text_ops.str_extract,
    'str_case': text_ops.str_case,
    'str_contains': text_ops.str_contains,
    
    # NLP (New)
    'tokenize': nlp_ops.tokenize_text,
    'word_count': nlp_ops.count_words,
    'ngrams': nlp_ops.generate_ngrams,

    # Stats
    'zscore': stat_ops.calculate_zscore,
    'rank': stat_ops.rank_data,
    'clip': stat_ops.clip_values,
    
    # Math (New)
    'math': math_ops.apply_math,
    'minmax_scale': math_ops.normalize_minmax,
    'std_scale': math_ops.standardize_scale,
    
    # Feature Eng (New)
    'interactions': feature_ops.create_interactions,
    'poly': feature_ops.polynomial_features,

    # Quality (New)
    'validate': quality_ops.validate_schema,
    'check_constraints': quality_ops.check_constraints,
    'drop_outliers': quality_ops.remove_outliers_iqr,
    'drop_empty_cols': quality_ops.drop_empty_cols,

    # IO
    'convert': io_ops.convert_dataset
}

# Mapping of which argument receives the "current file path" in the chain
INPUT_ARG_MAP = {
    'merge': 'left_path',
    'concat': None, # Manual handling needed as it takes a list
    'default': 'file_path'
}

def execute_chain(initial_file_path: str, steps: List[Dict[str, Any]], final_output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes a chain of pandas operations on a dataset.
    
    Args:
        initial_file_path: Starting file.
        steps: List of dicts, e.g. [{"op": "filter", "args": {"query": "age > 25"}}].
        final_output_path: Where to save the final result. If None, returns the temp path.
    """
    current_path = initial_file_path
    cleanup_files = []
    
    try:
        for i, step in enumerate(steps):
            op_name = step.get('op')
            args = step.get('args', {}).copy()
            
            if op_name not in OP_MAP:
                raise ValueError(f"Unknown operation: {op_name}")
            
            func = OP_MAP[op_name]
            
            # Determine output path for this step
            if i == len(steps) - 1 and final_output_path:
                step_output = final_output_path
            else:
                # Create a temp file
                # Preserve extension if possible, or default to parquet for intermediate efficiency
                # but parquet requires pyarrow. Let's stick to the input extension or parquet if safe.
                ext = os.path.splitext(current_path)[1]
                if not ext: ext = ".parquet" # Default
                
                step_output = f"temp_chain_{uuid.uuid4().hex}{ext}"
                cleanup_files.append(step_output)
            
            # Inject input path
            input_arg = INPUT_ARG_MAP.get(op_name, INPUT_ARG_MAP['default'])
            if input_arg:
                args[input_arg] = current_path
            
            # Inject output path
            args['output_path'] = step_output
            
            # Execute
            logger.info("executing_step", step=i, op=op_name, input=current_path, output=step_output)
            func(**args)
            
            # Update current path for next step
            current_path = step_output
            
        return {
            "status": "success",
            "final_output": current_path,
            "steps_executed": len(steps),
            "temp_files_created": cleanup_files # Caller can decide to delete them
        }
        
    except Exception as e:
        logger.error("chain_execution_failed", error=str(e), step_index=i)
        raise RuntimeError(f"Chain failed at step {i} ({op_name}): {str(e)}")
