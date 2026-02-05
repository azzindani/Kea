from mcp_servers.networkx_server.tools.core_ops import to_serializable
import networkx as nx
from typing import Dict, Any, List, Optional

# Classic
async def complete_graph(n: int) -> Dict[str, Any]:
    return to_serializable(nx.complete_graph(n))

async def cycle_graph(n: int) -> Dict[str, Any]:
    return to_serializable(nx.cycle_graph(n))

async def path_graph(n: int) -> Dict[str, Any]:
    return to_serializable(nx.path_graph(n))

async def star_graph(n: int) -> Dict[str, Any]:
    return to_serializable(nx.star_graph(n))

async def grid_2d_graph(m: int, n: int) -> Dict[str, Any]:
    # Grid nodes are tuples (0,1), flatten for easier JSON?
    # NetworkX JSON handles tuple keys by converting to string or list usually
    # But nx.node_link_data might warn. Let's relabel to integers for safety in standard MCP
    g = nx.grid_2d_graph(m, n)
    g = nx.convert_node_labels_to_integers(g)
    return to_serializable(g)

async def karate_club_graph() -> Dict[str, Any]:
    return to_serializable(nx.karate_club_graph())

# Random
async def erdos_renyi_graph(n: int, p: float, seed: Optional[int] = None) -> Dict[str, Any]:
    return to_serializable(nx.erdos_renyi_graph(n, p, seed=seed))

async def watts_strogatz_graph(n: int, k: int, p: float, seed: Optional[int] = None) -> Dict[str, Any]:
    return to_serializable(nx.watts_strogatz_graph(n, k, p, seed=seed))

async def barabasi_albert_graph(n: int, m: int, seed: Optional[int] = None) -> Dict[str, Any]:
    return to_serializable(nx.barabasi_albert_graph(n, m, seed=seed))

async def random_regular_graph(d: int, n: int, seed: Optional[int] = None) -> Dict[str, Any]:
    return to_serializable(nx.random_regular_graph(d, n, seed=seed))

async def fast_gnp_random_graph(n: int, p: float, seed: Optional[int] = None) -> Dict[str, Any]:
    return to_serializable(nx.fast_gnp_random_graph(n, p, seed=seed))
