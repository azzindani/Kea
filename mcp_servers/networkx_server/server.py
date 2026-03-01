
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "mcp",
#   "networkx",
#   "numpy",
#   "pandas",
#   "scipy",
#   "structlog",
# ]
# ///

from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.networkx_server.tools import (
    basic_ops, gen_ops, path_ops, centrality_ops, 
    community_ops, linalg_ops, io_ops, super_ops
)
import structlog
from typing import List, Dict, Any, Optional, Union

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging(force_stderr=True)

mcp = FastMCP("networkx_server", dependencies=["networkx", "scipy", "numpy", "pandas"])
GraphInput = Union[List[List[Any]], Dict[str, Any], str]

# ==========================================
# 1. Basics
# ==========================================
# ==========================================
# 1. Basics
# ==========================================
@mcp.tool()
async def create_graph(data: Optional[GraphInput] = None, directed: bool = False) -> Dict[str, Any]: 
    """CREATES graph. [ACTION]
    
    [RAG Context]
    Create a new NetworkX graph (directed or undirected).
    Returns JSON dict (adjacency).
    """
    return await basic_ops.create_graph(data, directed)

@mcp.tool()
async def add_nodes(graph: GraphInput, nodes: List[Any]) -> Dict[str, Any]: 
    """ADDS nodes. [ACTION]
    
    [RAG Context]
    Add nodes to existing graph.
    Returns JSON dict (updated graph).
    """
    return await basic_ops.add_nodes(graph, nodes)

@mcp.tool()
async def add_edges(graph: GraphInput, edges: List[List[Any]]) -> Dict[str, Any]: 
    """ADDS edges. [ACTION]
    
    [RAG Context]
    Add edges to existing graph.
    Returns JSON dict (updated graph).
    """
    return await basic_ops.add_edges(graph, edges)

@mcp.tool()
async def graph_info(graph: GraphInput) -> Dict[str, Any]: 
    """FETCHES graph info. [ACTION]
    
    [RAG Context]
    Get number of nodes, edges, density, etc.
    Returns JSON dict.
    """
    return await basic_ops.graph_info(graph)

@mcp.tool()
async def get_nodes(graph: GraphInput, data: bool = False) -> List[Any]: 
    """FETCHES nodes. [ACTION]
    
    [RAG Context]
    Get list of nodes in graph (with optional data).
    Returns list.
    """
    return await basic_ops.get_nodes(graph, data)

@mcp.tool()
async def get_edges(graph: GraphInput, data: bool = False) -> List[Any]: 
    """FETCHES edges. [ACTION]
    
    [RAG Context]
    Get list of edges in graph (with optional data).
    Returns list.
    """
    return await basic_ops.get_edges(graph, data)

@mcp.tool()
async def degree(graph: GraphInput, nbunch: Optional[List[Any]] = None) -> Dict[Any, int]: 
    """CALCULATES degree. [ACTION]
    
    [RAG Context]
    Get degree (number of edges) for nodes.
    Returns JSON dict.
    """
    return await basic_ops.degree(graph, nbunch)

@mcp.tool()
async def neighbors(graph: GraphInput, n: Any) -> List[Any]: 
    """FETCHES neighbors. [ACTION]
    
    [RAG Context]
    Get neighbors of a specific node.
    Returns list.
    """
    return await basic_ops.neighbors(graph, n)

@mcp.tool()
async def subgraph(graph: GraphInput, nodes: List[Any]) -> Dict[str, Any]: 
    """CREATES subgraph. [ACTION]
    
    [RAG Context]
    Create a subgraph containing only specified nodes.
    Returns JSON dict.
    """
    return await basic_ops.subgraph(graph, nodes)

@mcp.tool()
async def is_directed(graph: GraphInput) -> bool: 
    """CHECKS directed. [ACTION]
    
    [RAG Context]
    Check if graph is directed.
    Returns boolean.
    """
    return await basic_ops.is_directed(graph)

@mcp.tool()
async def is_connected(graph: GraphInput) -> bool: 
    """CHECKS connected. [ACTION]
    
    [RAG Context]
    Check if graph is fully connected.
    Returns boolean.
    """
    return await basic_ops.is_connected(graph)

# ==========================================
# 2. Generators
# ==========================================
@mcp.tool()
async def complete_graph(n: int) -> Dict[str, Any]: 
    """GENERATES complete graph. [ACTION]
    
    [RAG Context]
    Create graph where every node is connected to every other.
    Returns JSON dict.
    """
    return await gen_ops.complete_graph(n)

@mcp.tool()
async def cycle_graph(n: int) -> Dict[str, Any]: 
    """GENERATES cycle graph. [ACTION]
    
    [RAG Context]
    Create graph capable of a single cycle.
    Returns JSON dict.
    """
    return await gen_ops.cycle_graph(n)

@mcp.tool()
async def path_graph(n: int) -> Dict[str, Any]: 
    """GENERATES path graph. [ACTION]
    
    [RAG Context]
    Create graph as a linear path of n nodes.
    Returns JSON dict.
    """
    return await gen_ops.path_graph(n)

@mcp.tool()
async def star_graph(n: int) -> Dict[str, Any]: 
    """GENERATES star graph. [ACTION]
    
    [RAG Context]
    Create graph with one center node connected to n outer nodes.
    Returns JSON dict.
    """
    return await gen_ops.star_graph(n)

@mcp.tool()
async def grid_2d_graph(m: int, n: int) -> Dict[str, Any]: 
    """GENERATES grid graph. [ACTION]
    
    [RAG Context]
    Create a 2D grid graph (lattice).
    Returns JSON dict.
    """
    return await gen_ops.grid_2d_graph(m, n)

@mcp.tool()
async def karate_club_graph() -> Dict[str, Any]: 
    """GENERATES Karate Club. [ACTION]
    
    [RAG Context]
    Create the famous Zachary's Karate Club graph.
    Returns JSON dict.
    """
    return await gen_ops.karate_club_graph()

@mcp.tool()
async def erdos_renyi_graph(n: int, p: float, seed: Optional[int] = None) -> Dict[str, Any]: 
    """GENERATES Erdos-Renyi. [ACTION]
    
    [RAG Context]
    Create random graph with probability p.
    Returns JSON dict.
    """
    return await gen_ops.erdos_renyi_graph(n, p, seed)

@mcp.tool()
async def watts_strogatz_graph(n: int, k: int, p: float, seed: Optional[int] = None) -> Dict[str, Any]: 
    """GENERATES Watts-Strogatz. [ACTION]
    
    [RAG Context]
    Create small-world graph.
    Returns JSON dict.
    """
    return await gen_ops.watts_strogatz_graph(n, k, p, seed)

@mcp.tool()
async def barabasi_albert_graph(n: int, m: int, seed: Optional[int] = None) -> Dict[str, Any]: 
    """GENERATES Barabasi-Albert. [ACTION]
    
    [RAG Context]
    Create scale-free graph using preferential attachment.
    Returns JSON dict.
    """
    return await gen_ops.barabasi_albert_graph(n, m, seed)

@mcp.tool()
async def random_regular_graph(d: int, n: int, seed: Optional[int] = None) -> Dict[str, Any]: 
    """GENERATES random regular. [ACTION]
    
    [RAG Context]
    Create d-regular random graph.
    Returns JSON dict.
    """
    return await gen_ops.random_regular_graph(d, n, seed)

@mcp.tool()
async def fast_gnp_random_graph(n: int, p: float, seed: Optional[int] = None) -> Dict[str, Any]: 
    """GENERATES fast GNP. [ACTION]
    
    [RAG Context]
    Create random graph (faster algorithm).
    Returns JSON dict.
    """
    return await gen_ops.fast_gnp_random_graph(n, p, seed)

# ==========================================
# 3. Path & Traversal
# ==========================================
# ==========================================
# 3. Path & Traversal
# ==========================================
@mcp.tool()
async def shortest_path(graph: GraphInput, source: Any, target: Any, weight: Optional[str] = None) -> List[Any]: 
    """CALCULATES shortest path. [ACTION]
    
    [RAG Context]
    Find shortest path between source and target.
    Returns list of nodes.
    """
    return await path_ops.shortest_path(graph, source, target, weight)

@mcp.tool()
async def shortest_path_length(graph: GraphInput, source: Any, target: Any, weight: Optional[str] = None) -> Union[int, float]: 
    """CALCULATES path length. [ACTION]
    
    [RAG Context]
    Get length of shortest path.
    Returns number.
    """
    return await path_ops.shortest_path_length(graph, source, target, weight)

@mcp.tool()
async def all_shortest_paths(graph: GraphInput, source: Any, target: Any, weight: Optional[str] = None) -> List[List[Any]]: 
    """FETCHES all shortest paths. [ACTION]
    
    [RAG Context]
    Get all valid shortest paths between nodes.
    Returns list of paths (lists).
    """
    return await path_ops.all_shortest_paths(graph, source, target, weight)

@mcp.tool()
async def has_path(graph: GraphInput, source: Any, target: Any) -> bool: 
    """CHECKS path existence. [ACTION]
    
    [RAG Context]
    Check if a path exists between nodes.
    Returns boolean.
    """
    return await path_ops.has_path(graph, source, target)

@mcp.tool()
async def minimum_spanning_tree(graph: GraphInput, weight: str = 'weight', algorithm: str = 'kruskal') -> Dict[str, Any]: 
    """CALCULATES MST. [ACTION]
    
    [RAG Context]
    Find Minimum Spanning Tree of graph.
    Returns JSON dict.
    """
    return await path_ops.minimum_spanning_tree(graph, weight, algorithm)

@mcp.tool()
async def bfs_tree(graph: GraphInput, source: Any, depth_limit: Optional[int] = None) -> Dict[str, Any]: 
    """GENERATES BFS tree. [ACTION]
    
    [RAG Context]
    Breadth-First Search tree from source.
    Returns JSON dict.
    """
    return await path_ops.bfs_tree(graph, source, depth_limit)

@mcp.tool()
async def dfs_tree(graph: GraphInput, source: Any, depth_limit: Optional[int] = None) -> Dict[str, Any]: 
    """GENERATES DFS tree. [ACTION]
    
    [RAG Context]
    Depth-First Search tree from source.
    Returns JSON dict.
    """
    return await path_ops.dfs_tree(graph, source, depth_limit)

@mcp.tool()
async def diameter(graph: GraphInput) -> int: 
    """CALCULATES diameter. [ACTION]
    
    [RAG Context]
    Get maximum eccentricity of graph.
    Returns int.
    """
    return await path_ops.diameter(graph)

@mcp.tool()
async def radius(graph: GraphInput) -> int: 
    """CALCULATES radius. [ACTION]
    
    [RAG Context]
    Get minimum eccentricity of graph.
    Returns int.
    """
    return await path_ops.radius(graph)

# ==========================================
# 4. Centrality
# ==========================================
# ==========================================
# 4. Centrality
# ==========================================
@mcp.tool()
async def degree_centrality(graph: GraphInput) -> Dict[Any, float]: 
    """CALCULATES degree centrality. [ACTION]
    
    [RAG Context]
    Compute degree centrality for nodes.
    Returns JSON dict.
    """
    return await centrality_ops.degree_centrality(graph)

@mcp.tool()
async def betweenness_centrality(graph: GraphInput, k: Optional[int] = None, normalized: bool = True, weight: Optional[str] = None) -> Dict[Any, float]: 
    """CALCULATES betweenness. [ACTION]
    
    [RAG Context]
    Compute betweenness centrality.
    Returns JSON dict.
    """
    return await centrality_ops.betweenness_centrality(graph, k, normalized, weight)

@mcp.tool()
async def closeness_centrality(graph: GraphInput, u: Optional[Any] = None, distance: Optional[str] = None) -> Union[float, Dict[Any, float]]: 
    """CALCULATES closeness. [ACTION]
    
    [RAG Context]
    Compute closeness centrality.
    Returns JSON dict (or float).
    """
    return await centrality_ops.closeness_centrality(graph, u, distance)

@mcp.tool()
async def eigenvector_centrality(graph: GraphInput, max_iter: int = 100, tol: float = 1e-06, weight: Optional[str] = None) -> Dict[Any, float]: 
    """CALCULATES eigenvector. [ACTION]
    
    [RAG Context]
    Compute eigenvector centrality.
    Returns JSON dict.
    """
    return await centrality_ops.eigenvector_centrality(graph, max_iter, tol, weight)

@mcp.tool()
async def pagerank(graph: GraphInput, alpha: float = 0.85, weight: str = 'weight') -> Dict[Any, float]: 
    """CALCULATES PageRank. [ACTION]
    
    [RAG Context]
    Compute PageRank of nodes.
    Returns JSON dict.
    """
    return await centrality_ops.pagerank(graph, alpha, weight)

@mcp.tool()
async def hits(graph: GraphInput, max_iter: int = 100, tol: float = 1e-08, normalized: bool = True) -> Dict[str, Dict[Any, float]]: 
    """CALCULATES HITS. [ACTION]
    
    [RAG Context]
    Compute HITS hubs and authorities.
    Returns JSON dict.
    """
    return await centrality_ops.hits(graph, max_iter, tol, normalized)

# ==========================================
# 5. Community
# ==========================================
# ==========================================
# 5. Community
# ==========================================
@mcp.tool()
async def clustering(graph: GraphInput, nodes: Optional[List[Any]] = None, weight: Optional[str] = None) -> Dict[Any, float]: 
    """CALCULATES clustering. [ACTION]
    
    [RAG Context]
    Compute clustering coefficient for nodes.
    Returns JSON dict.
    """
    return await community_ops.clustering(graph, nodes, weight)

@mcp.tool()
async def average_clustering(graph: GraphInput, weight: Optional[str] = None) -> float: 
    """CALCULATES avg clustering. [ACTION]
    
    [RAG Context]
    Compute average clustering coefficient.
    Returns float.
    """
    return await community_ops.average_clustering(graph, weight)

@mcp.tool()
async def transitivity(graph: GraphInput) -> float: 
    """CALCULATES transitivity. [ACTION]
    
    [RAG Context]
    Compute graph transitivity.
    Returns float.
    """
    return await community_ops.transitivity(graph)

@mcp.tool()
async def connected_components(graph: GraphInput) -> List[List[Any]]: 
    """FETCHES connected components. [ACTION]
    
    [RAG Context]
    Find connected components in undirected graph.
    Returns list of lists.
    """
    return await community_ops.connected_components(graph)

@mcp.tool()
async def strongly_connected_components(graph: GraphInput) -> List[List[Any]]: 
    """FETCHES strong components. [ACTION]
    
    [RAG Context]
    Find strongly connected components in directed graph.
    Returns list of lists.
    """
    return await community_ops.strongly_connected_components(graph)

@mcp.tool()
async def weakly_connected_components(graph: GraphInput) -> List[List[Any]]: 
    """FETCHES weak components. [ACTION]
    
    [RAG Context]
    Find weakly connected components in directed graph.
    Returns list of lists.
    """
    return await community_ops.weakly_connected_components(graph)

@mcp.tool()
async def find_cliques(graph: GraphInput) -> List[List[Any]]: 
    """FINDS cliques. [ACTION]
    
    [RAG Context]
    Find all maximal cliques in graph.
    Returns list of lists.
    """
    return await community_ops.find_cliques(graph)

@mcp.tool()
async def louvain_communities(graph: GraphInput, weight: str = 'weight', resolution: float = 1.0) -> List[List[Any]]: 
    """DETECTS Louvain communities. [ACTION]
    
    [RAG Context]
    Detect communities using Louvain method.
    Returns list of lists.
    """
    return await community_ops.louvain_communities(graph, weight, resolution)

@mcp.tool()
async def greedy_modularity_communities(graph: GraphInput, weight: Optional[str] = None, resolution: float = 1) -> List[List[Any]]: 
    """DETECTS greedy modularity. [ACTION]
    
    [RAG Context]
    Detect communities using greedy modularity.
    Returns list of lists.
    """
    return await community_ops.greedy_modularity_communities(graph, weight, resolution)

@mcp.tool()
async def bridges(graph: GraphInput, root: Optional[Any] = None) -> List[Any]: 
    """FINDS bridges. [ACTION]
    
    [RAG Context]
    Find all bridges in graph.
    Returns list of edges.
    """
    return await community_ops.bridges(graph, root)

# ==========================================
# 6. Linalg
# ==========================================
# ==========================================
# 6. Linalg
# ==========================================
@mcp.tool()
async def adjacency_matrix(graph: GraphInput, weight: str = 'weight') -> List[List[float]]: 
    """CALCULATES adjacency matrix. [ACTION]
    
    [RAG Context]
    Get adjacency matrix of graph.
    Returns list of lists (matrix).
    """
    return await linalg_ops.adjacency_matrix(graph, weight)

@mcp.tool()
async def laplacian_matrix(graph: GraphInput, weight: str = 'weight') -> List[List[float]]: 
    """CALCULATES Laplacian. [ACTION]
    
    [RAG Context]
    Get Laplacian matrix of graph.
    Returns list of lists (matrix).
    """
    return await linalg_ops.laplacian_matrix(graph, weight)

@mcp.tool()
async def modularity_matrix(graph: GraphInput, nodelist: Optional[List[Any]] = None, weight: str = 'weight') -> List[List[float]]: 
    """CALCULATES modularity. [ACTION]
    
    [RAG Context]
    Get modularity matrix.
    Returns list of lists (matrix).
    """
    return await linalg_ops.modularity_matrix(graph, nodelist, weight)

@mcp.tool()
async def adjacency_spectrum(graph: GraphInput, weight: str = 'weight') -> List[complex]: 
    """CALCULATES adjacency spectrum. [ACTION]
    
    [RAG Context]
    Get eigenvalues of adjacency matrix.
    Returns list of complex numbers.
    """
    return await linalg_ops.adjacency_spectrum(graph, weight)

@mcp.tool()
async def laplacian_spectrum(graph: GraphInput, weight: str = 'weight') -> List[float]: 
    """CALCULATES Laplacian spectrum. [ACTION]
    
    [RAG Context]
    Get eigenvalues of Laplacian matrix.
    Returns list of floats.
    """
    return await linalg_ops.laplacian_spectrum(graph, weight)

@mcp.tool()
async def algebraic_connectivity(graph: GraphInput, weight: str = 'weight') -> float: 
    """CALCULATES connectivity. [ACTION]
    
    [RAG Context]
    Get algebraic connectivity (Fiedler value).
    Returns float.
    """
    return await linalg_ops.algebraic_connectivity(graph, weight)

# ==========================================
# 7. IO & Super
# ==========================================
@mcp.tool()
async def read_graph(data: str, format: str = 'json') -> Dict[str, Any]: 
    """READS graph. [ACTION]
    
    [RAG Context]
    Read graph from JSON, GML, etc.
    Returns JSON dict.
    """
    return await io_ops.read_graph(data, format)

@mcp.tool()
async def write_graph(graph: GraphInput, format: str = 'json') -> str: 
    """WRITES graph. [ACTION]
    
    [RAG Context]
    Write graph to string in specified format.
    Returns string.
    """
    return await io_ops.write_graph(graph, format)

@mcp.tool()
async def analyze_graph(graph: GraphInput) -> Dict[str, Any]: 
    """ANALYZES graph. [ACTION]
    
    [RAG Context]
    Comprehensive graph analysis (shape, stats, centrality).
    Returns JSON dict.
    """
    return await super_ops.analyze_graph(graph)

@mcp.tool()
async def structure_dashboard(graph: GraphInput) -> Dict[str, Any]: 
    """GENERATES dashboard. [ACTION]
    
    [RAG Context]
    High-level structural overview of graph.
    Returns JSON dict.
    """
    return await super_ops.structure_dashboard(graph)

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class NetworkxServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []

