from mcp_servers.scipy_server.tools.core_ops import parse_data, to_serializable, NumericData
from scipy import special
from typing import List, Any, Union

async def gamma_func(z: NumericData) -> List[float]:
    """Gamma function."""
    arr = parse_data(z)
    return to_serializable(special.gamma(arr).tolist())

async def beta_func(a: NumericData, b: NumericData) -> List[float]:
    """Beta function."""
    a_arr = parse_data(a)
    b_arr = parse_data(b)
    return to_serializable(special.beta(a_arr, b_arr).tolist())

async def erf_func(z: NumericData) -> List[float]:
    """Error function."""
    arr = parse_data(z)
    return to_serializable(special.erf(arr).tolist())

async def bessel_j0(z: NumericData) -> List[float]:
    """Bessel function of the first kind of order 0."""
    arr = parse_data(z)
    return to_serializable(special.j0(arr).tolist())
