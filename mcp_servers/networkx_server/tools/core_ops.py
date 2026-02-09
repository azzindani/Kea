import networkx as nx
import structlog
from typing import Any, List, Union, Optional, Dict, Tuple
import json
import ast

logger = structlog.get_logger()

# Common types
# GraphInput can be:
# - Edge List: [[1, 2], [2, 3]]
# - Adjacency Dict: {"1": ["2"], "2": ["3"]}
# - Node-Link JSON: {"nodes": [{"id": 1}], "links": [{"source": 1, "target": 2}]}
GraphInput = Union[List[List[Any]], Dict[str, Any], str]

def _unwrap_fastmcp(data: Any) -> Any:
    """Extract graph data from a fastmcp response envelope if present."""
    if isinstance(data, dict) and "status" in data and "data" in data:
        return data["data"]
    return data

def parse_graph(data: GraphInput, directed: bool = False) -> nx.Graph:
    """
    Parse input data into a NetworkX Graph or DiGraph.
    """
    g_cls = nx.DiGraph if directed else nx.Graph

    try:
        if isinstance(data, str):
            # Try JSON parsing first, then Python literal as fallback
            try:
                parsed = json.loads(data)
            except json.JSONDecodeError:
                try:
                    parsed = ast.literal_eval(data)
                except (ValueError, SyntaxError):
                    raise ValueError("Input string is not valid JSON or Python literal.")
        else:
            parsed = data

        # Unwrap fastmcp response envelope if present
        parsed = _unwrap_fastmcp(parsed)

        # 1. Edge List (List of Lists/Tuples)
        if isinstance(parsed, list):
            # Assume edge list
            return nx.from_edgelist(parsed, create_using=g_cls)
        
        # 2. Dict (Adjacency or Node-Link)
        if isinstance(parsed, dict):
            # Check for Node-Link format (d3.js style)
            if "nodes" in parsed and ("links" in parsed or "edges" in parsed):
                return nx.node_link_graph(parsed, directed=directed)
            
            # Check for Adjacency Dict
            # parsing dict of lists/dicts
            return nx.from_dict_of_lists(parsed, create_using=g_cls)
            
        raise ValueError(f"Unknown graph data format: {type(parsed)}")
            
    except Exception as e:
        logger.error("graph_parsing_failed", error=str(e))
        raise ValueError(f"Could not parse input data to Graph: {str(e)}")

def to_serializable(data: Any) -> Any:
    """Convert NetworkX/Numpy types to Python native types."""
    import numpy as np
    
    if isinstance(data, (nx.Graph, nx.DiGraph)):
        # Return Node-Link JSON format by default for full graph objects
        return nx.node_link_data(data)
    elif isinstance(data, (np.integer, int)):
        return int(data)
    elif isinstance(data, (np.floating, float)):
        return float(data)
    elif isinstance(data, np.ndarray):
        return data.tolist()
    elif isinstance(data, dict):
        return {k: to_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [to_serializable(v) for v in data]
    elif isinstance(data, set):
        return [to_serializable(v) for v in list(data)]
    elif isinstance(data, tuple):
        return list(data) # Tuples to lists for JSON
    return data
