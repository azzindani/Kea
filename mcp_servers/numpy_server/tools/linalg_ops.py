from mcp_servers.numpy_server.tools.core_ops import parse_array, to_serializable, NumericData
import numpy as np
from typing import Dict, Any, List, Optional, Union

async def dot(a: NumericData, b: NumericData) -> List[Any]:
    return to_serializable(np.dot(parse_array(a), parse_array(b)).tolist())

async def matmul(x1: NumericData, x2: NumericData) -> List[Any]:
    return to_serializable(np.matmul(parse_array(x1), parse_array(x2)).tolist())

async def inner(a: NumericData, b: NumericData) -> List[Any]:
    return to_serializable(np.inner(parse_array(a), parse_array(b)).tolist())

async def outer(a: NumericData, b: NumericData) -> List[Any]:
    return to_serializable(np.outer(parse_array(a), parse_array(b)).tolist())

async def kron(a: NumericData, b: NumericData) -> List[Any]:
    return to_serializable(np.kron(parse_array(a), parse_array(b)).tolist())

async def matrix_power(a: NumericData, n: int) -> List[Any]:
    return to_serializable(np.linalg.matrix_power(parse_array(a), n).tolist())

async def cholesky(a: NumericData) -> List[Any]:
    return to_serializable(np.linalg.cholesky(parse_array(a)).tolist())

async def qr_decomp(a: NumericData, mode: str = 'reduced') -> Dict[str, Any]:
    q, r = np.linalg.qr(parse_array(a), mode=mode)
    return to_serializable({"q": q.tolist(), "r": r.tolist()})

async def svd_decomp(a: NumericData, full_matrices: bool = True) -> Dict[str, Any]:
    u, s, vh = np.linalg.svd(parse_array(a), full_matrices=full_matrices)
    return to_serializable({"u": u.tolist(), "s": s.tolist(), "vh": vh.tolist()})

async def eig(a: NumericData) -> Dict[str, Any]:
    w, v = np.linalg.eig(parse_array(a))
    # Complex support via standard serialization (core_ops doesn't explicitly convert complex to string yet in simple to_serializable, 
    # but to_serializable uses str() fall back for unknown types, so complex -> string representation)
    # Ideally split real/imag, but complex string is often parsable back.
    # Let's clean up for JSON if possible.
    return {
        "eigenvalues": [str(x) for x in w.tolist()],
        "eigenvectors": [[str(y) for y in x] for x in v.tolist()]
    }

async def norm(x: NumericData, ord: Any = None, axis: Any = None) -> float:
    return float(np.linalg.norm(parse_array(x), ord=ord, axis=axis))

async def cond(x: NumericData, p: Any = None) -> float:
    return float(np.linalg.cond(parse_array(x), p=p))

async def det(a: NumericData) -> float:
    return float(np.linalg.det(parse_array(a)))

async def matrix_rank(M: NumericData) -> int:
    return int(np.linalg.matrix_rank(parse_array(M)))

async def solve(a: NumericData, b: NumericData) -> List[Any]:
    return to_serializable(np.linalg.solve(parse_array(a), parse_array(b)).tolist())

async def inv(a: NumericData) -> List[Any]:
    return to_serializable(np.linalg.inv(parse_array(a)).tolist())

async def pinv(a: NumericData) -> List[Any]:
    return to_serializable(np.linalg.pinv(parse_array(a)).tolist())

async def lstsq(a: NumericData, b: NumericData, rcond: str = 'warn') -> Dict[str, Any]:
    sol = np.linalg.lstsq(parse_array(a), parse_array(b), rcond=None if rcond=='warn' else float(rcond))
    return to_serializable({
        "solution": sol[0].tolist(),
        "residuals": sol[1].tolist(),
        "rank": int(sol[2]),
        "singular_values": sol[3].tolist()
    })
