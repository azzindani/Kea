from mcp_servers.networkx_server.tools.core_ops import parse_graph, to_serializable, GraphInput
import networkx as nx
import numpy as np
import scipy.sparse
from typing import Dict, Any, List, Optional, Union

# Helper to handle sparse matrices -> list
def _mat_to_list(mat) -> List[List[float]]:
    if scipy.sparse.issparse(mat):
        return mat.toarray().tolist()
    return mat.tolist()

async def adjacency_matrix(graph: GraphInput, weight: str = 'weight') -> List[List[float]]:
    """Return adjacency matrix."""
    g = parse_graph(graph)
    return to_serializable(_mat_to_list(nx.adjacency_matrix(g, weight=weight)))

async def laplacian_matrix(graph: GraphInput, weight: str = 'weight') -> List[List[float]]:
    """Return Laplacian matrix."""
    g = parse_graph(graph)
    return to_serializable(_mat_to_list(nx.laplacian_matrix(g, weight=weight)))

async def modularity_matrix(graph: GraphInput, nodelist: Optional[List[Any]] = None, weight: str = 'weight') -> List[List[float]]:
    """Return modularity matrix."""
    g = parse_graph(graph)
    return to_serializable(_mat_to_list(nx.modularity_matrix(g, nodelist=nodelist, weight=weight)))

async def adjacency_spectrum(graph: GraphInput, weight: str = 'weight') -> List[complex]:
    """Return eigenvalues of the adjacency matrix."""
    g = parse_graph(graph)
    return to_serializable(nx.adjacency_spectrum(g, weight=weight).tolist())

async def laplacian_spectrum(graph: GraphInput, weight: str = 'weight') -> List[float]:
    """Return eigenvalues of the Laplacian matrix."""
    g = parse_graph(graph)
    return to_serializable(nx.laplacian_spectrum(g, weight=weight).tolist())

async def algebraic_connectivity(graph: GraphInput, weight: str = 'weight') -> float:
    """Return the algebraic connectivity of the graph."""
    g = parse_graph(graph)
    return to_serializable(nx.algebraic_connectivity(g, weight=weight))
