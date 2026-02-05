from mcp_servers.networkx_server.tools.core_ops import parse_graph, to_serializable, GraphInput
import networkx as nx
from typing import Dict, Any, List, Optional, Union

async def degree_centrality(graph: GraphInput) -> Dict[Any, float]:
    """Compute the degree centrality for nodes."""
    g = parse_graph(graph)
    return to_serializable(nx.degree_centrality(g))

async def betweenness_centrality(graph: GraphInput, k: Optional[int] = None, normalized: bool = True, weight: Optional[str] = None) -> Dict[Any, float]:
    """Compute the shortest-path betweenness centrality for nodes."""
    g = parse_graph(graph)
    return to_serializable(nx.betweenness_centrality(g, k=k, normalized=normalized, weight=weight))

async def closeness_centrality(graph: GraphInput, u: Optional[Any] = None, distance: Optional[str] = None) -> Union[float, Dict[Any, float]]:
    """Compute closeness centrality for nodes."""
    g = parse_graph(graph)
    return to_serializable(nx.closeness_centrality(g, u=u, distance=distance))

async def eigenvector_centrality(graph: GraphInput, max_iter: int = 100, tol: float = 1e-06, weight: Optional[str] = None) -> Dict[Any, float]:
    """Compute the eigenvector centrality for the graph G."""
    g = parse_graph(graph)
    return to_serializable(nx.eigenvector_centrality(g, max_iter=max_iter, tol=tol, weight=weight))

async def pagerank(graph: GraphInput, alpha: float = 0.85, weight: str = 'weight') -> Dict[Any, float]:
    """Return the PageRank of the nodes in the graph."""
    g = parse_graph(graph)
    return to_serializable(nx.pagerank(g, alpha=alpha, weight=weight))

async def hits(graph: GraphInput, max_iter: int = 100, tol: float = 1e-08, normalized: bool = True) -> Dict[str, Dict[Any, float]]:
    """Return HITS hubs and authorities values for nodes."""
    g = parse_graph(graph)
    hubs, authorities = nx.hits(g, max_iter=max_iter, tol=tol, normalized=normalized)
    return to_serializable({"hubs": hubs, "authorities": authorities})
