from mcp_servers.networkx_server.tools.core_ops import parse_graph, to_serializable, GraphInput
import networkx as nx
from typing import Dict, Any, List, Optional, Union

async def shortest_path(graph: GraphInput, source: Any, target: Any, weight: Optional[str] = None) -> List[Any]:
    """Compute shortest path between source and target."""
    g = parse_graph(graph)
    return to_serializable(nx.shortest_path(g, source=source, target=target, weight=weight))

async def shortest_path_length(graph: GraphInput, source: Any, target: Any, weight: Optional[str] = None) -> Union[int, float]:
    """Compute shortest path length."""
    g = parse_graph(graph)
    return to_serializable(nx.shortest_path_length(g, source=source, target=target, weight=weight))

async def all_shortest_paths(graph: GraphInput, source: Any, target: Any, weight: Optional[str] = None) -> List[List[Any]]:
    """Compute all shortest paths."""
    g = parse_graph(graph)
    return to_serializable(list(nx.all_shortest_paths(g, source=source, target=target, weight=weight)))

async def has_path(graph: GraphInput, source: Any, target: Any) -> bool:
    """Return True if G has a path from source to target."""
    g = parse_graph(graph)
    return nx.has_path(g, source, target)

async def minimum_spanning_tree(graph: GraphInput, weight: str = 'weight', algorithm: str = 'kruskal') -> Dict[str, Any]:
    """Returns a minimum spanning tree or forest on an undirected graph."""
    g = parse_graph(graph)
    # MST defined for undirected
    if g.is_directed():
        g = g.to_undirected()
    mst = nx.minimum_spanning_tree(g, weight=weight, algorithm=algorithm)
    return to_serializable(mst)

async def bfs_tree(graph: GraphInput, source: Any, depth_limit: Optional[int] = None) -> Dict[str, Any]:
    """Returns an oriented tree constructed from of a breadth-first-search starting at source."""
    g = parse_graph(graph)
    tree = nx.bfs_tree(g, source, depth_limit=depth_limit)
    return to_serializable(tree)

async def dfs_tree(graph: GraphInput, source: Any, depth_limit: Optional[int] = None) -> Dict[str, Any]:
    """Returns an oriented tree constructed from of a depth-first-search starting at source."""
    g = parse_graph(graph)
    tree = nx.dfs_tree(g, source, depth_limit=depth_limit)
    return to_serializable(tree)

async def diameter(graph: GraphInput) -> int:
    """Return the diameter of the graph."""
    g = parse_graph(graph)
    return nx.diameter(g)

async def radius(graph: GraphInput) -> int:
    """Return the radius of the graph."""
    g = parse_graph(graph)
    return nx.radius(g)
