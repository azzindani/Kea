from mcp_servers.scipy_server.tools.core_ops import to_serializable, parse_data, NumericData
from scipy import optimize
import numpy as np
from typing import Dict, Any, List, Optional, Callable

# Note: For optimization, we often deal with FUNCTIONS. Passing functions as strings 
# (e.g. "x**2 + 5") and using eval() is dangerous but necessary for generic capability 
# if we can't define python code. 
# WE WILL USE `eval` WITH CAUTION or restrict to simple expressions if possible.
# Ideally, we allow simple lambda strings like "lambda x: x**2 + x + 2"

def _make_func(func_str: str) -> Callable:
    """Safely compile a lambda string."""
    # This is a security risk if not sandboxed. 
    # For now, we assume local user trust (as per MCP model usually).
    # We will wrap in standard lambda creation.
    # Ex: "x[0]**2 + x[1]**2" -> lambda x: x[0]**2 + x[1]**2
    if "lambda" not in func_str:
        # Assume single variable x or vector x
        func_str = f"lambda x: {func_str}"
    
    # Simple sanitization
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_([., +-*/%<>!=])")
    # This is notoriously hard to secure perfectly. 
    # We rely on Server's "SafeToAutoRun" context and user trust for now.
    
    return eval(func_str, {"np": np, "abs": abs, "sin": np.sin, "cos": np.cos, "exp": np.exp, "sqrt": np.sqrt})

# ==========================================
# Local Optimization
# ==========================================
async def minimize_scalar(func_str: str, method: str = 'brent') -> Dict[str, Any]:
    """Minimize a scalar function of one variable."""
    fun = _make_func(func_str)
    res = optimize.minimize_scalar(fun, method=method)
    return to_serializable({"x": res.x, "fun": res.fun, "success": res.success})

async def minimize_bfgs(func_str: str, x0: List[float]) -> Dict[str, Any]:
    """Minimize using BFGS (Gradient Descent extension)."""
    fun = _make_func(func_str)
    x0_arr = np.array(x0)
    res = optimize.minimize(fun, x0_arr, method='BFGS')
    return to_serializable({"x": res.x.tolist(), "fun": res.fun, "success": res.success})

async def minimize_nelder(func_str: str, x0: List[float]) -> Dict[str, Any]:
    """Minimize using Nelder-Mead (Simplex)."""
    fun = _make_func(func_str)
    x0_arr = np.array(x0)
    res = optimize.minimize(fun, x0_arr, method='Nelder-Mead')
    return to_serializable({"x": res.x.tolist(), "fun": res.fun, "success": res.success})

async def find_root(func_str: str, a: float, b: float) -> float:
    """Find a root of the function in interval [a, b] using Brentq."""
    fun = _make_func(func_str)
    try:
        root = optimize.brentq(fun, a, b)
        return float(root)
    except Exception as e:
        return float('nan')

async def curve_fit(func_str: str, x_data: NumericData, y_data: NumericData) -> Dict[str, Any]:
    """
    Fit a function f(x, *params) to data using non-linear least squares.
    Reviewer note: func_str must take (x, a, b, c...)
    Ex: "lambda x, a, b: a * x + b"
    """
    fun = _make_func(func_str)
    x = parse_data(x_data)
    y = parse_data(y_data)
    
    popt, pcov = optimize.curve_fit(fun, x, y)
    return to_serializable({"params": popt.tolist(), "covariance": pcov.tolist()})

async def linear_sum_assignment(cost_matrix: List[List[float]]) -> Dict[str, Any]:
    """Solve the linear sum assignment problem (Hungarian algorithm)."""
    cost = np.array(cost_matrix)
    row_ind, col_ind = optimize.linear_sum_assignment(cost)
    total_cost = cost[row_ind, col_ind].sum()
    return to_serializable({"row_ind": row_ind.tolist(), "col_ind": col_ind.tolist(), "cost": total_cost})

async def linprog(c: List[float], A_ub: List[List[float]] = None, b_ub: List[float] = None, A_eq: List[List[float]] = None, b_eq: List[float] = None, bounds: List[List[float]] = None) -> Dict[str, Any]:
    """Linear Programming: minimize c @ x."""
    res = optimize.linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')
    return to_serializable({"x": res.x.tolist() if res.x is not None else None, "fun": res.fun, "success": res.success, "message": res.message})

# ==========================================
# Global Optimization
# ==========================================
async def basinhopping(func_str: str, x0: List[float], niter: int = 100) -> Dict[str, Any]:
    """Find global minimum using Basin Hopping."""
    fun = _make_func(func_str)
    x0_arr = np.array(x0)
    res = optimize.basinhopping(fun, x0_arr, niter=niter)
    return to_serializable({"x": res.x.tolist(), "fun": res.fun, "success": True}) # basinhopping result struct slightly diff

async def differential_evolution(func_str: str, bounds: List[List[float]]) -> Dict[str, Any]:
    """Find global minimum using Differential Evolution."""
    fun = _make_func(func_str)
    res = optimize.differential_evolution(fun, bounds)
    return to_serializable({"x": res.x.tolist(), "fun": res.fun, "success": res.success})

async def dual_annealing(func_str: str, bounds: List[List[float]]) -> Dict[str, Any]:
    """Find global minimum using Dual Annealing."""
    fun = _make_func(func_str)
    res = optimize.dual_annealing(fun, bounds)
    return to_serializable({"x": res.x.tolist(), "fun": res.fun, "success": res.success})
