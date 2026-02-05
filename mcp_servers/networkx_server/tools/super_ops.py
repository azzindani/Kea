from mcp_servers.networkx_server.tools.core_ops import parse_graph, to_serializable, GraphInput
import networkx as nx
import numpy as np
from typing import Dict, Any, List, Optional

async def analyze_graph(graph: GraphInput) -> Dict[str, Any]:
    """
    Super Tool: Comprehensive graph analysis report.
    Returns size, density, connectivity info, and basic stats.
    """
    g = parse_graph(graph)
    
    is_directed = g.is_directed()
    is_connected = nx.is_weakly_connected(g) if is_directed else nx.is_connected(g)
    
    report = {
        "basic": {
            "nodes": g.number_of_nodes(),
            "edges": g.number_of_edges(),
            "density": float(nx.density(g)),
            "is_directed": is_directed,
            "is_connected": is_connected
        },
        "degrees": {
            "avg_degree": sum(dict(g.degree()).values()) / g.number_of_nodes() if g.number_of_nodes() > 0 else 0
        }
    }
    
    # Components
    if is_directed:
        report["components"] = {
            "strongly_connected": nx.number_strongly_connected_components(g),
            "weakly_connected": nx.number_weakly_connected_components(g)
        }
    else:
        report["components"] = nx.number_connected_components(g)
        
    return to_serializable(report)

async def structure_dashboard(graph: GraphInput) -> Dict[str, Any]:
    """
    Super Tool: Advanced structural metrics.
    Triangles, Transitivity, Clustering, Diameter (if connected).
    """
    g = parse_graph(graph)
    if g.is_directed():
        g_undir = g.to_undirected()
    else:
        g_undir = g
        
    res = {
        "transitivity": float(nx.transitivity(g)),
        "avg_clustering": float(nx.average_clustering(g)),
        "triangles": sum(nx.triangles(g_undir).values()) / 3
    }
    
    try:
        if nx.is_connected(g_undir):
            res["diameter"] = nx.diameter(g_undir)
            res["radius"] = nx.radius(g_undir)
            res["avg_shortest_path"] = nx.average_shortest_path_length(g_undir)
        else:
            res["diameter"] = "inf"
    except:
        pass
        
    return to_serializable(res)
