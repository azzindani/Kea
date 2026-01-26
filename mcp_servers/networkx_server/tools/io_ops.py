from mcp_servers.networkx_server.tools.core_ops import parse_graph, to_serializable, GraphInput
import networkx as nx
from typing import Dict, Any, List, Optional, Union

async def read_graph(data: str, format: str = 'json') -> Dict[str, Any]:
    """
    Parse string data into a graph and return standard JSON representation.
    Supported formats: 'json' (node-link), 'gml', 'graphml', 'edgelist'.
    """
    g = nx.Graph()
    try:
        if format == 'json':
            # Rely on core parser
            g = parse_graph(data)
        elif format == 'gml':
             g = nx.parse_gml(data)
        elif format == 'graphml':
             g = nx.parse_graphml(data)
        elif format == 'edgelist':
             g = nx.parse_edgelist(data.splitlines())
        else:
            return {"error": f"Unsupported format: {format}"}
            
        return to_serializable(g)
    except Exception as e:
        return {"error": str(e)}

async def write_graph(graph: GraphInput, format: str = 'json') -> str:
    """
    Export graph to string format.
    Supported: 'json', 'gml', 'graphml', 'edgelist'.
    """
    g = parse_graph(graph)
    try:
        if format == 'json':
            import json
            return json.dumps(to_serializable(g))
        elif format == 'gml':
            return "\n".join(nx.generate_gml(g))
        elif format == 'graphml':
            # NetworkX returns bytes or path usually, generate_graphml yields lines
            return "\n".join(nx.generate_graphml(g))
        elif format == 'edgelist':
            return "\n".join(nx.generate_edgelist(g))
        else:
            return f"Error: Unsupported format {format}"
    except Exception as e:
        return f"Error exporting graph: {str(e)}"
