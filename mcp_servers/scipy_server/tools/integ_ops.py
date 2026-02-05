from mcp_servers.scipy_server.tools.core_ops import to_serializable, parse_data, NumericData
from scipy import integrate
import numpy as np
from typing import Dict, Any, List, Optional, Callable

def _make_func(func_str: str) -> Callable:
    if "lambda" not in func_str:
        func_str = f"lambda x: {func_str}"
    return eval(func_str, {"np": np, "abs": abs, "sin": np.sin, "cos": np.cos, "exp": np.exp, "sqrt": np.sqrt})

async def integrate_quad(func_str: str, a: float, b: float) -> Dict[str, float]:
    """Calculate definite integral of f(x) from a to b using QUADPACK."""
    fun = _make_func(func_str)
    res, err = integrate.quad(fun, a, b)
    return {"result": float(res), "error": float(err)}

async def integrate_simpson(y_data: NumericData, x_data: Optional[NumericData] = None, dx: float = 1.0) -> float:
    """Integrate y(x) samples using Simpson's rule."""
    y = parse_data(y_data)
    if x_data:
        x = parse_data(x_data)
        return float(integrate.simpson(y, x=x))
    else:
        return float(integrate.simpson(y, dx=dx))

async def integrate_trapezoid(y_data: NumericData, x_data: Optional[NumericData] = None, dx: float = 1.0) -> float:
    """Integrate y(x) samples using Trapezoidal rule."""
    y = parse_data(y_data)
    if x_data:
        x = parse_data(x_data)
        return float(integrate.trapezoid(y, x=x))
    else:
        return float(integrate.trapezoid(y, dx=dx))

async def solve_ivp(func_str: str, t_span: List[float], y0: List[float], t_eval: List[float] = None) -> Dict[str, Any]:
    """
    Solve Initial Value Problem (ODE). 
    dy/dt = f(t, y).
    func_str must accept (t, y). E.g. "lambda t, y: -0.5 * y"
    """
    # Note: func must be lambda t, y
    if "lambda" not in func_str:
        # User might provide just expression assuming t,y vars
        func_str = f"lambda t, y: {func_str}"
        
    fun = _make_func(func_str)
    
    res = integrate.solve_ivp(fun, t_span, y0, t_eval=t_eval)
    
    return to_serializable({
        "t": res.t.tolist(),
        "y": res.y.tolist(),
        "success": res.success,
        "message": res.message
    })
