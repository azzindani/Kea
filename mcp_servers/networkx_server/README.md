# 🔌 Networkx Server

The `networkx_server` is an MCP server providing tools for **Networkx Server** functionality.
It is designed to be used within the Kea ecosystem.

## 🧰 Tools

| Tool | Description | Arguments |
|:-----|:------------|:----------|
| `create_graph` | Execute create graph operation | `data: Optional[GraphInput] = None, directed: bool = False` |
| `add_nodes` | Execute add nodes operation | `graph: GraphInput, nodes: List[Any]` |
| `add_edges` | Execute add edges operation | `graph: GraphInput, edges: List[List[Any]]` |
| `graph_info` | Execute graph info operation | `graph: GraphInput` |
| `get_nodes` | Execute get nodes operation | `graph: GraphInput, data: bool = False` |
| `get_edges` | Execute get edges operation | `graph: GraphInput, data: bool = False` |
| `degree` | Execute degree operation | `graph: GraphInput, nbunch: Optional[List[Any]] = None` |
| `neighbors` | Execute neighbors operation | `graph: GraphInput, n: Any` |
| `subgraph` | Execute subgraph operation | `graph: GraphInput, nodes: List[Any]` |
| `is_directed` | Execute is directed operation | `graph: GraphInput` |
| `is_connected` | Execute is connected operation | `graph: GraphInput` |
| `complete_graph` | Execute complete graph operation | `n: int` |
| `cycle_graph` | Execute cycle graph operation | `n: int` |
| `path_graph` | Execute path graph operation | `n: int` |
| `star_graph` | Execute star graph operation | `n: int` |
| `grid_2d_graph` | Execute grid 2d graph operation | `m: int, n: int` |
| `karate_club_graph` | Execute karate club graph operation | `` |
| `erdos_renyi_graph` | Execute erdos renyi graph operation | `n: int, p: float, seed: Optional[int] = None` |
| `watts_strogatz_graph` | Execute watts strogatz graph operation | `n: int, k: int, p: float, seed: Optional[int] = None` |
| `barabasi_albert_graph` | Execute barabasi albert graph operation | `n: int, m: int, seed: Optional[int] = None` |
| `random_regular_graph` | Execute random regular graph operation | `d: int, n: int, seed: Optional[int] = None` |
| `fast_gnp_random_graph` | Execute fast gnp random graph operation | `n: int, p: float, seed: Optional[int] = None` |
| `shortest_path` | Execute shortest path operation | `graph: GraphInput, source: Any, target: Any, weight: Optional[str] = None` |
| `shortest_path_length` | Execute shortest path length operation | `graph: GraphInput, source: Any, target: Any, weight: Optional[str] = None` |
| `all_shortest_paths` | Execute all shortest paths operation | `graph: GraphInput, source: Any, target: Any, weight: Optional[str] = None` |
| `has_path` | Execute has path operation | `graph: GraphInput, source: Any, target: Any` |
| `minimum_spanning_tree` | Execute minimum spanning tree operation | `graph: GraphInput, weight: str = 'weight', algorithm: str = 'kruskal'` |
| `bfs_tree` | Execute bfs tree operation | `graph: GraphInput, source: Any, depth_limit: Optional[int] = None` |
| `dfs_tree` | Execute dfs tree operation | `graph: GraphInput, source: Any, depth_limit: Optional[int] = None` |
| `diameter` | Execute diameter operation | `graph: GraphInput` |
| `radius` | Execute radius operation | `graph: GraphInput` |
| `degree_centrality` | Execute degree centrality operation | `graph: GraphInput` |
| `betweenness_centrality` | Execute betweenness centrality operation | `graph: GraphInput, k: Optional[int] = None, normalized: bool = True, weight: Optional[str] = None` |
| `closeness_centrality` | Execute closeness centrality operation | `graph: GraphInput, u: Optional[Any] = None, distance: Optional[str] = None` |
| `eigenvector_centrality` | Execute eigenvector centrality operation | `graph: GraphInput, max_iter: int = 100, tol: float = 1e-06, weight: Optional[str] = None` |
| `pagerank` | Execute pagerank operation | `graph: GraphInput, alpha: float = 0.85, weight: str = 'weight'` |
| `hits` | Execute hits operation | `graph: GraphInput, max_iter: int = 100, tol: float = 1e-08, normalized: bool = True` |
| `clustering` | Execute clustering operation | `graph: GraphInput, nodes: Optional[List[Any]] = None, weight: Optional[str] = None` |
| `average_clustering` | Execute average clustering operation | `graph: GraphInput, weight: Optional[str] = None` |
| `transitivity` | Execute transitivity operation | `graph: GraphInput` |
| `connected_components` | Execute connected components operation | `graph: GraphInput` |
| `strongly_connected_components` | Execute strongly connected components operation | `graph: GraphInput` |
| `weakly_connected_components` | Execute weakly connected components operation | `graph: GraphInput` |
| `find_cliques` | Execute find cliques operation | `graph: GraphInput` |
| `louvain_communities` | Execute louvain communities operation | `graph: GraphInput, weight: str = 'weight', resolution: float = 1.0` |
| `greedy_modularity_communities` | Execute greedy modularity communities operation | `graph: GraphInput, weight: Optional[str] = None, resolution: float = 1` |
| `bridges` | Execute bridges operation | `graph: GraphInput, root: Optional[Any] = None` |
| `adjacency_matrix` | Execute adjacency matrix operation | `graph: GraphInput, weight: str = 'weight'` |
| `laplacian_matrix` | Execute laplacian matrix operation | `graph: GraphInput, weight: str = 'weight'` |
| `modularity_matrix` | Execute modularity matrix operation | `graph: GraphInput, nodelist: Optional[List[Any]] = None, weight: str = 'weight'` |
| `adjacency_spectrum` | Execute adjacency spectrum operation | `graph: GraphInput, weight: str = 'weight'` |
| `laplacian_spectrum` | Execute laplacian spectrum operation | `graph: GraphInput, weight: str = 'weight'` |
| `algebraic_connectivity` | Execute algebraic connectivity operation | `graph: GraphInput, weight: str = 'weight'` |
| `read_graph` | Execute read graph operation | `data: str, format: str = 'json'` |
| `write_graph` | Execute write graph operation | `graph: GraphInput, format: str = 'json'` |
| `analyze_graph` | Execute analyze graph operation | `graph: GraphInput` |
| `structure_dashboard` | Execute structure dashboard operation | `graph: GraphInput` |

## 📦 Dependencies

The following packages are required:
- `networkx`
- `scipy`
- `numpy`
- `pandas`

## 🚀 Usage

This server is automatically discovered by the **MCP Host**. To run it manually:

```bash
uv run python -m mcp_servers.networkx_server.server
```
