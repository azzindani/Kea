from mcp_servers.numpy_server.tools.core_ops import parse_array, to_serializable, NumericData
import numpy as np
from numpy.polynomial import Polynomial
from typing import Dict, Any, List, Optional, Union

# Using the modern numpy.polynomial.Polynomial API
# Coefficients order: increasing (lowest degree first). [1, 2, 3] -> 1 + 2x + 3x^2

async def poly_fit(x: NumericData, y: NumericData, deg: int) -> Dict[str, Any]:
    """
    Fit a polynomial to data using least squares.
    Returns coefficients (lowest degree first).
    """
    x_arr = parse_array(x)
    y_arr = parse_array(y)
    
    # Polynomial.fit returns a Series instance
    p = Polynomial.fit(x_arr, y_arr, deg)
    
    return to_serializable({
        "coef": p.coef.tolist(), 
        "domain": p.domain.tolist(),
        "window": p.window.tolist()
    })

async def poly_val(coef: List[float], x: NumericData) -> List[float]:
    """
    Evaluate a polynomial with specific coefficients at x.
    coef example: [1, 2, 3] means 1 + 2x + 3x^2
    """
    p = Polynomial(coef)
    res = p(parse_array(x))
    return to_serializable(res.tolist())

async def poly_roots(coef: List[float]) -> List[Any]:
    """Find roots of the polynomial."""
    p = Polynomial(coef)
    return to_serializable(p.roots().tolist())

async def poly_from_roots(roots: List[float]) -> List[float]:
    """Construct a polynomial from its roots."""
    p = Polynomial.fromroots(roots)
    return to_serializable(p.coef.tolist())

async def poly_derivative(coef: List[float], m: int = 1) -> List[float]:
    """Calculate the m-th derivative."""
    p = Polynomial(coef)
    der = p.deriv(m=m)
    return to_serializable(der.coef.tolist())

async def poly_integrate(coef: List[float], m: int = 1) -> List[float]:
    """Calculate the m-th integral."""
    p = Polynomial(coef)
    integ = p.integ(m=m)
    return to_serializable(integ.coef.tolist())
