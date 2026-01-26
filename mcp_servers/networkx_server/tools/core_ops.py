import networkx as nx
import structlog
from typing import Any, List, Union, Optional, Dict, Tuple
import json

logger = structlog.get_logger()

# Common types
# GraphInput can be:
# - Edge List: [[1, 2], [2, 3]]
# - Adjacency Dict: {"1": ["2"], "2": ["3"]}
# - Node-Link JSON: {"nodes": [{"id": 1}], "links": [{"source": 1, "target": 2}]}
GraphInput = Union[List[List[Any]], Dict[str, Any], str]

def parse_graph(data: GraphInput, directed: bool = False) -> nx.Graph:
    """
    Parse input data into a NetworkX Graph or DiGraph.
    """
    g_cls = nx.DiGraph if directed else nx.Graph
    
    try:
        if isinstance(data, str):
            # Try JSON parsing first
            try:
                parsed = json.loads(data)
            except json.JSONDecodeError:
                raise ValueError("Input string is not valid JSON.")
        else:
            parsed = data

        # 1. Edge List (List of Lists/Tuples)
        if isinstance(parsed, list):
            # Assume edge list
            return nx.from_edgelist(parsed, create_using=g_cls)
        
        # 2. Dict (Adjacency or Node-Link)
        if isinstance(parsed, dict):
            # Check for Node-Link format (d3.js style)
            if "nodes" in parsed and "links" in parsed:
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
