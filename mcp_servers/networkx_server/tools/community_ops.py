from mcp_servers.networkx_server.tools.core_ops import parse_graph, to_serializable, GraphInput
import networkx as nx
from typing import Dict, Any, List, Optional, Union

async def clustering(graph: GraphInput, nodes: Optional[List[Any]] = None, weight: Optional[str] = None) -> Dict[Any, float]:
    """Compute the clustering coefficient for nodes."""
    g = parse_graph(graph)
    return to_serializable(nx.clustering(g, nodes=nodes, weight=weight))

async def average_clustering(graph: GraphInput, weight: Optional[str] = None) -> float:
    """Compute the average clustering coefficient for the graph G."""
    g = parse_graph(graph)
    return to_serializable(nx.average_clustering(g, weight=weight))

async def transitivity(graph: GraphInput) -> float:
    """Compute graph transitivity, the fraction of all possible triangles present in G."""
    g = parse_graph(graph)
    return to_serializable(nx.transitivity(g))

async def connected_components(graph: GraphInput) -> List[List[Any]]:
    """Generate connected components."""
    g = parse_graph(graph)
    return to_serializable(list(nx.connected_components(g)))

async def strongly_connected_components(graph: GraphInput) -> List[List[Any]]:
    """Generate strongly connected components."""
    g = parse_graph(graph, directed=True)
    return to_serializable(list(nx.strongly_connected_components(g)))

async def weakly_connected_components(graph: GraphInput) -> List[List[Any]]:
    """Generate weakly connected components."""
    g = parse_graph(graph, directed=True)
    return to_serializable(list(nx.weakly_connected_components(g)))

async def find_cliques(graph: GraphInput) -> List[List[Any]]:
    """Returns all maximal cliques in an undirected graph."""
    g = parse_graph(graph)
    # Undirected only
    return to_serializable(list(nx.find_cliques(g.to_undirected())))

async def louvain_communities(graph: GraphInput, weight: str = 'weight', resolution: float = 1.0) -> List[List[Any]]:
    """Find the best partition of a graph using the Louvain Community Detection Algorithm."""
    g = parse_graph(graph)
    # Returns list of sets
    return to_serializable(nx.community.louvain_communities(g, weight=weight, resolution=resolution))

async def greedy_modularity_communities(graph: GraphInput, weight: Optional[str] = None, resolution: float = 1) -> List[List[Any]]:
    """Find communities in graph using Clauset-Newman-Moore greedy modularity maximization."""
    g = parse_graph(graph)
    return to_serializable(nx.community.greedy_modularity_communities(g, weight=weight, resolution=resolution))

async def bridges(graph: GraphInput, root: Optional[Any] = None) -> List[Any]:
    """Generate all bridges in a graph."""
    g = parse_graph(graph)
    return to_serializable(list(nx.bridges(g, root=root)))
