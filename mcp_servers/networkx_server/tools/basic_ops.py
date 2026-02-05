from mcp_servers.networkx_server.tools.core_ops import parse_graph, to_serializable, GraphInput
import networkx as nx
from typing import Dict, Any, List, Optional, Union, Tuple

async def create_graph(data: Optional[GraphInput] = None, directed: bool = False) -> Dict[str, Any]:
    """Create a graph, optionally from data, and return its node-link JSON."""
    if data:
        g = parse_graph(data, directed=directed)
    else:
        g = nx.DiGraph() if directed else nx.Graph()
    return to_serializable(g)

async def add_nodes(graph: GraphInput, nodes: List[Any]) -> Dict[str, Any]:
    """Add nodes to the graph."""
    g = parse_graph(graph)
    g.add_nodes_from(nodes)
    return to_serializable(g)

async def add_edges(graph: GraphInput, edges: List[List[Any]]) -> Dict[str, Any]:
    """Add edges to the graph. Edges should be [u, v] or [u, v, weight]."""
    g = parse_graph(graph)
    g.add_edges_from(edges)
    return to_serializable(g)

async def graph_info(graph: GraphInput) -> Dict[str, Any]:
    """Return basic information about the graph."""
    g = parse_graph(graph)
    return to_serializable({
        "number_of_nodes": g.number_of_nodes(),
        "number_of_edges": g.number_of_edges(),
        "density": nx.density(g),
        "is_directed": g.is_directed(),
        "is_multigraph": g.is_multigraph()
    })

async def get_nodes(graph: GraphInput, data: bool = False) -> List[Any]:
    """List nodes of the graph."""
    g = parse_graph(graph)
    return to_serializable(list(g.nodes(data=data)))

async def get_edges(graph: GraphInput, data: bool = False) -> List[Any]:
    """List edges of the graph."""
    g = parse_graph(graph)
    return to_serializable(list(g.edges(data=data)))

async def degree(graph: GraphInput, nbunch: Optional[List[Any]] = None) -> Dict[Any, int]:
    """Report the degree of nodes."""
    g = parse_graph(graph)
    return to_serializable(dict(g.degree(nbunch)))

async def neighbors(graph: GraphInput, n: Any) -> List[Any]:
    """Return a list of nodes connected to node n."""
    g = parse_graph(graph)
    # n must be mapped to correct type if JSON stringified inputs?
    # Usually inputs match graph node types.
    return to_serializable(list(g.neighbors(n)))

async def subgraph(graph: GraphInput, nodes: List[Any]) -> Dict[str, Any]:
    """Return the subgraph induced on nodes."""
    g = parse_graph(graph)
    sub = g.subgraph(nodes)
    return to_serializable(sub)

async def is_directed(graph: GraphInput) -> bool:
    """Return True if graph is directed."""
    g = parse_graph(graph)
    return g.is_directed()

async def is_connected(graph: GraphInput) -> bool:
    """Return True if graph is connected (or weakly connected for digraphs)."""
    g = parse_graph(graph)
    if g.is_directed():
        return nx.is_weakly_connected(g)
    return nx.is_connected(g)
