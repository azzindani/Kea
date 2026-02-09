from mcp_servers.scipy_server.tools.core_ops import to_serializable, parse_data, compile_function, NumericData
from scipy import integrate
import numpy as np
from typing import Dict, Any, List, Optional, Callable

async def integrate_quad(func_str: str, a: float, b: float) -> Dict[str, float]:
    """Calculate definite integral of f(x) from a to b using QUADPACK."""
    fun = compile_function(func_str)
    res, err = integrate.quad(fun, a, b)
    # res might be a list/tuple depending on quad variation, but usually (y, abserr)
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
    func_str must accept (t, y). E.g. "lambda t, y: -0.5 * y" or just "-0.5 * y"
    """
    fun = compile_function(func_str, required_vars=['t', 'y'])
    
    res = integrate.solve_ivp(fun, t_span, y0, t_eval=t_eval)
    
    return to_serializable({
        "t": res.t.tolist(),
        "y": res.y.tolist(),
        "success": res.success,
        "message": res.message
    })
