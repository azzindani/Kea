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

from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from tools import (
    basic_ops, gen_ops, path_ops, centrality_ops, 
    community_ops, linalg_ops, io_ops, super_ops
)
import structlog
from typing import List, Dict, Any, Optional, Union

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("networkx_server", dependencies=["networkx", "scipy", "numpy", "pandas"])
GraphInput = Union[List[List[Any]], Dict[str, Any], str]

# ==========================================
# 1. Basics
# ==========================================
@mcp.tool()
async def create_graph(data: Optional[GraphInput] = None, directed: bool = False) -> Dict[str, Any]: return await basic_ops.create_graph(data, directed)
@mcp.tool()
async def add_nodes(graph: GraphInput, nodes: List[Any]) -> Dict[str, Any]: return await basic_ops.add_nodes(graph, nodes)
@mcp.tool()
async def add_edges(graph: GraphInput, edges: List[List[Any]]) -> Dict[str, Any]: return await basic_ops.add_edges(graph, edges)
@mcp.tool()
async def graph_info(graph: GraphInput) -> Dict[str, Any]: return await basic_ops.graph_info(graph)
@mcp.tool()
async def get_nodes(graph: GraphInput, data: bool = False) -> List[Any]: return await basic_ops.get_nodes(graph, data)
@mcp.tool()
async def get_edges(graph: GraphInput, data: bool = False) -> List[Any]: return await basic_ops.get_edges(graph, data)
@mcp.tool()
async def degree(graph: GraphInput, nbunch: Optional[List[Any]] = None) -> Dict[Any, int]: return await basic_ops.degree(graph, nbunch)
@mcp.tool()
async def neighbors(graph: GraphInput, n: Any) -> List[Any]: return await basic_ops.neighbors(graph, n)
@mcp.tool()
async def subgraph(graph: GraphInput, nodes: List[Any]) -> Dict[str, Any]: return await basic_ops.subgraph(graph, nodes)
@mcp.tool()
async def is_directed(graph: GraphInput) -> bool: return await basic_ops.is_directed(graph)
@mcp.tool()
async def is_connected(graph: GraphInput) -> bool: return await basic_ops.is_connected(graph)

# ==========================================
# 2. Generators
# ==========================================
@mcp.tool()
async def complete_graph(n: int) -> Dict[str, Any]: return await gen_ops.complete_graph(n)
@mcp.tool()
async def cycle_graph(n: int) -> Dict[str, Any]: return await gen_ops.cycle_graph(n)
@mcp.tool()
async def path_graph(n: int) -> Dict[str, Any]: return await gen_ops.path_graph(n)
@mcp.tool()
async def star_graph(n: int) -> Dict[str, Any]: return await gen_ops.star_graph(n)
@mcp.tool()
async def grid_2d_graph(m: int, n: int) -> Dict[str, Any]: return await gen_ops.grid_2d_graph(m, n)
@mcp.tool()
async def karate_club_graph() -> Dict[str, Any]: return await gen_ops.karate_club_graph()
@mcp.tool()
async def erdos_renyi_graph(n: int, p: float, seed: Optional[int] = None) -> Dict[str, Any]: return await gen_ops.erdos_renyi_graph(n, p, seed)
@mcp.tool()
async def watts_strogatz_graph(n: int, k: int, p: float, seed: Optional[int] = None) -> Dict[str, Any]: return await gen_ops.watts_strogatz_graph(n, k, p, seed)
@mcp.tool()
async def barabasi_albert_graph(n: int, m: int, seed: Optional[int] = None) -> Dict[str, Any]: return await gen_ops.barabasi_albert_graph(n, m, seed)
@mcp.tool()
async def random_regular_graph(d: int, n: int, seed: Optional[int] = None) -> Dict[str, Any]: return await gen_ops.random_regular_graph(d, n, seed)
@mcp.tool()
async def fast_gnp_random_graph(n: int, p: float, seed: Optional[int] = None) -> Dict[str, Any]: return await gen_ops.fast_gnp_random_graph(n, p, seed)

# ==========================================
# 3. Path & Traversal
# ==========================================
@mcp.tool()
async def shortest_path(graph: GraphInput, source: Any, target: Any, weight: Optional[str] = None) -> List[Any]: return await path_ops.shortest_path(graph, source, target, weight)
@mcp.tool()
async def shortest_path_length(graph: GraphInput, source: Any, target: Any, weight: Optional[str] = None) -> Union[int, float]: return await path_ops.shortest_path_length(graph, source, target, weight)
@mcp.tool()
async def all_shortest_paths(graph: GraphInput, source: Any, target: Any, weight: Optional[str] = None) -> List[List[Any]]: return await path_ops.all_shortest_paths(graph, source, target, weight)
@mcp.tool()
async def has_path(graph: GraphInput, source: Any, target: Any) -> bool: return await path_ops.has_path(graph, source, target)
@mcp.tool()
async def minimum_spanning_tree(graph: GraphInput, weight: str = 'weight', algorithm: str = 'kruskal') -> Dict[str, Any]: return await path_ops.minimum_spanning_tree(graph, weight, algorithm)
@mcp.tool()
async def bfs_tree(graph: GraphInput, source: Any, depth_limit: Optional[int] = None) -> Dict[str, Any]: return await path_ops.bfs_tree(graph, source, depth_limit)
@mcp.tool()
async def dfs_tree(graph: GraphInput, source: Any, depth_limit: Optional[int] = None) -> Dict[str, Any]: return await path_ops.dfs_tree(graph, source, depth_limit)
@mcp.tool()
async def diameter(graph: GraphInput) -> int: return await path_ops.diameter(graph)
@mcp.tool()
async def radius(graph: GraphInput) -> int: return await path_ops.radius(graph)

# ==========================================
# 4. Centrality
# ==========================================
@mcp.tool()
async def degree_centrality(graph: GraphInput) -> Dict[Any, float]: return await centrality_ops.degree_centrality(graph)
@mcp.tool()
async def betweenness_centrality(graph: GraphInput, k: Optional[int] = None, normalized: bool = True, weight: Optional[str] = None) -> Dict[Any, float]: return await centrality_ops.betweenness_centrality(graph, k, normalized, weight)
@mcp.tool()
async def closeness_centrality(graph: GraphInput, u: Optional[Any] = None, distance: Optional[str] = None) -> Union[float, Dict[Any, float]]: return await centrality_ops.closeness_centrality(graph, u, distance)
@mcp.tool()
async def eigenvector_centrality(graph: GraphInput, max_iter: int = 100, tol: float = 1e-06, weight: Optional[str] = None) -> Dict[Any, float]: return await centrality_ops.eigenvector_centrality(graph, max_iter, tol, weight)
@mcp.tool()
async def pagerank(graph: GraphInput, alpha: float = 0.85, weight: str = 'weight') -> Dict[Any, float]: return await centrality_ops.pagerank(graph, alpha, weight)
@mcp.tool()
async def hits(graph: GraphInput, max_iter: int = 100, tol: float = 1e-08, normalized: bool = True) -> Dict[str, Dict[Any, float]]: return await centrality_ops.hits(graph, max_iter, tol, normalized)

# ==========================================
# 5. Community
# ==========================================
@mcp.tool()
async def clustering(graph: GraphInput, nodes: Optional[List[Any]] = None, weight: Optional[str] = None) -> Dict[Any, float]: return await community_ops.clustering(graph, nodes, weight)
@mcp.tool()
async def average_clustering(graph: GraphInput, weight: Optional[str] = None) -> float: return await community_ops.average_clustering(graph, weight)
@mcp.tool()
async def transitivity(graph: GraphInput) -> float: return await community_ops.transitivity(graph)
@mcp.tool()
async def connected_components(graph: GraphInput) -> List[List[Any]]: return await community_ops.connected_components(graph)
@mcp.tool()
async def strongly_connected_components(graph: GraphInput) -> List[List[Any]]: return await community_ops.strongly_connected_components(graph)
@mcp.tool()
async def weakly_connected_components(graph: GraphInput) -> List[List[Any]]: return await community_ops.weakly_connected_components(graph)
@mcp.tool()
async def find_cliques(graph: GraphInput) -> List[List[Any]]: return await community_ops.find_cliques(graph)
@mcp.tool()
async def louvain_communities(graph: GraphInput, weight: str = 'weight', resolution: float = 1.0) -> List[List[Any]]: return await community_ops.louvain_communities(graph, weight, resolution)
@mcp.tool()
async def greedy_modularity_communities(graph: GraphInput, weight: Optional[str] = None, resolution: float = 1) -> List[List[Any]]: return await community_ops.greedy_modularity_communities(graph, weight, resolution)
@mcp.tool()
async def bridges(graph: GraphInput, root: Optional[Any] = None) -> List[Any]: return await community_ops.bridges(graph, root)

# ==========================================
# 6. Linalg
# ==========================================
@mcp.tool()
async def adjacency_matrix(graph: GraphInput, weight: str = 'weight') -> List[List[float]]: return await linalg_ops.adjacency_matrix(graph, weight)
@mcp.tool()
async def laplacian_matrix(graph: GraphInput, weight: str = 'weight') -> List[List[float]]: return await linalg_ops.laplacian_matrix(graph, weight)
@mcp.tool()
async def modularity_matrix(graph: GraphInput, nodelist: Optional[List[Any]] = None, weight: str = 'weight') -> List[List[float]]: return await linalg_ops.modularity_matrix(graph, nodelist, weight)
@mcp.tool()
async def adjacency_spectrum(graph: GraphInput, weight: str = 'weight') -> List[complex]: return await linalg_ops.adjacency_spectrum(graph, weight)
@mcp.tool()
async def laplacian_spectrum(graph: GraphInput, weight: str = 'weight') -> List[float]: return await linalg_ops.laplacian_spectrum(graph, weight)
@mcp.tool()
async def algebraic_connectivity(graph: GraphInput, weight: str = 'weight') -> float: return await linalg_ops.algebraic_connectivity(graph, weight)

# ==========================================
# 7. IO & Super
# ==========================================
@mcp.tool()
async def read_graph(data: str, format: str = 'json') -> Dict[str, Any]: return await io_ops.read_graph(data, format)
@mcp.tool()
async def write_graph(graph: GraphInput, format: str = 'json') -> str: return await io_ops.write_graph(graph, format)
@mcp.tool()
async def analyze_graph(graph: GraphInput) -> Dict[str, Any]: return await super_ops.analyze_graph(graph)
@mcp.tool()
async def structure_dashboard(graph: GraphInput) -> Dict[str, Any]: return await super_ops.structure_dashboard(graph)

if __name__ == "__main__":
    mcp.run()