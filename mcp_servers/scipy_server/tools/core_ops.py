import numpy as np
import structlog
from typing import Any, List, Union, Optional
import json
import re

logger = structlog.get_logger()

# Common type for numerical input
NumericData = Union[List[float], List[int], str] 

def compile_function(func_str: str, default_var: str = 'x', required_vars: Optional[List[str]] = None) -> Any:
    """
    Safely compile a string into a python function.
    Supports:
    - lambda x: ...
    - a*x + b (automatically detects parameters)
    - x[0]**2 (vector input)
    
    If required_vars is provided, they will be the first arguments in that order.
    Ex: required_vars=['t', 'y'] -> lambda t, y, a, b: ...
    """
    func_str = func_str.strip()
    
    # 1. If it's already a lambda, just eval it
    if "lambda" in func_str:
        return eval(func_str, {"np": np, "abs": abs, "sin": np.sin, "cos": np.cos, "exp": np.exp, "sqrt": np.sqrt})
    
    # 2. Try to detect parameters in expression
    # Use regex to find all variable-like words not in math/builtin list
    math_names = {"np", "abs", "sin", "cos", "exp", "sqrt", "log", "tan", "pi", "e"}
    words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', func_str)
    
    # Variables that are part of the "main" signature
    main_vars = required_vars if required_vars else [default_var]
    main_vars_set = set(main_vars)
    
    # Detect other parameters
    params = []
    for word in words:
        if word in math_names:
            continue
        if word in main_vars_set:
            continue
        if word not in params:
            params.append(word)
            
    # Reconstruct as lambda: lambda main_vars, params...: ...
    signature = ", ".join(main_vars + params)
        
    lambda_str = f"lambda {signature}: {func_str}"
    logger.debug("compiled_function", original=func_str, result=lambda_str)
    
    return eval(lambda_str, {"np": np, "abs": abs, "sin": np.sin, "cos": np.cos, "exp": np.exp, "sqrt": np.sqrt})

def parse_data(data: NumericData) -> np.ndarray:
    """
    Parse input data into a numpy array safely.
    Accepts: List, String (JSON or CSV-like).
    """
    try:
        if isinstance(data, str):
            # Try JSON first
            try:
                parsed = json.loads(data)
                return np.array(parsed, dtype=float)
            except json.JSONDecodeError:
                # Try simple comma-separated
                if "," in data:
                    return np.array([float(x.strip()) for x in data.split(",")], dtype=float)
                # Try space separated
                return np.array([float(x.strip()) for x in data.split()], dtype=float)
        
        return np.array(data, dtype=float)
    except Exception as e:
        logger.error("data_parsing_failed", error=str(e))
        raise ValueError(f"Could not parse input data to numpy array: {str(e)}")

def to_serializable(data: Any) -> Any:
    """Convert numpy types to Python native types for JSON serialization."""
    if isinstance(data, (np.integer, int)):
        return int(data)
    elif isinstance(data, (np.floating, float)):
        return float(data)
    elif isinstance(data, np.ndarray):
        return data.tolist()
    elif isinstance(data, dict):
        return {k: to_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [to_serializable(v) for v in data]
    return data
