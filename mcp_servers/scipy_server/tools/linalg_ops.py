from mcp_servers.scipy_server.tools.core_ops import to_serializable, parse_data, NumericData
from scipy import linalg
import numpy as np
from typing import Dict, Any, List

def _parse_matrix(data: Any) -> np.ndarray:
    return np.array(data)

async def matrix_inv(matrix: List[List[float]]) -> List[List[float]]:
    """Compute matrix inverse."""
    a = _parse_matrix(matrix)
    res = linalg.inv(a)
    return to_serializable(res.tolist())

async def matrix_det(matrix: List[List[float]]) -> float:
    """Compute determinant."""
    a = _parse_matrix(matrix)
    return float(linalg.det(a))

async def matrix_norm(matrix: List[List[float]], ord: str = None) -> float:
    """Compute matrix norm."""
    a = _parse_matrix(matrix)
    return float(linalg.norm(a, ord=None if ord=='None' else ord))

async def solve_linear(a: List[List[float]], b: List[float]) -> List[float]:
    """Solve Ax=b."""
    A_mat = _parse_matrix(a)
    b_vec = _parse_matrix(b)
    res = linalg.solve(A_mat, b_vec)
    return to_serializable(res.tolist())

async def svd_decomp(matrix: List[List[float]]) -> Dict[str, Any]:
    """Singular Value Decomposition."""
    a = _parse_matrix(matrix)
    U, s, Vh = linalg.svd(a)
    return to_serializable({"U": U.tolist(), "s": s.tolist(), "Vh": Vh.tolist()})

async def eig_decomp(matrix: List[List[float]]) -> Dict[str, Any]:
    """Eigenvalues and eigenvectors."""
    # Assuming square matrix
    a = _parse_matrix(matrix)
    vals, vecs = linalg.eig(a)
    # Eig results can be complex
    return to_serializable({
        "values_real": vals.real.tolist(), "values_imag": vals.imag.tolist(),
        "vectors_real": vecs.real.tolist(), "vectors_imag": vecs.imag.tolist()
    })

async def lu_factor(matrix: List[List[float]]) -> Dict[str, Any]:
    """LU Factorization."""
    a = _parse_matrix(matrix)
    lu, piv = linalg.lu_factor(a)
    return to_serializable({"lu": lu.tolist(), "piv": piv.tolist()})

async def cholesky(matrix: List[List[float]]) -> List[List[float]]:
    """Cholesky decomposition."""
    a = _parse_matrix(matrix)
    res = linalg.cholesky(a)
    return to_serializable(res.tolist())
