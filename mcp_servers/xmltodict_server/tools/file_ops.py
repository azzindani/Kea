import xmltodict
import json
import os
from typing import Dict, Any, List, Optional
from mcp_servers.xmltodict_server.tools import core_ops

# ====================
# File Ops
# ====================
def read_xml_file(file_path: str) -> Dict[str, Any]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return xmltodict.parse(f.read())
    except Exception as e:
        return {"error": str(e)}

def read_xml_file_no_attrs(file_path: str) -> Dict[str, Any]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return xmltodict.parse(f.read(), xml_attribs=False)
    except Exception as e:
        return {"error": str(e)}

def read_xml_config(file_path: str) -> Dict[str, Any]:
    """Optimized for config files (simple structure)."""
    return read_xml_file(file_path) # Wrapper

def read_rss_feed(file_path: str) -> Dict[str, Any]:
    """Parse RSS feed structure (force list on 'item')."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return xmltodict.parse(f.read(), force_list=('item',))
    except Exception as e:
        return {"error": str(e)}

def read_atom_feed(file_path: str) -> Dict[str, Any]:
    """Parse Atom feed (force list on 'entry')."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return xmltodict.parse(f.read(), force_list=('entry',))
    except Exception as e:
        return {"error": str(e)}

def read_svg_file(file_path: str) -> Dict[str, Any]:
    return read_xml_file(file_path)

def read_pom_xml(file_path: str) -> Dict[str, Any]:
    return read_xml_file(file_path)

def read_plist_xml(file_path: str) -> Dict[str, Any]:
    return read_xml_file(file_path)

def scan_xml_structure(file_path: str) -> str:
    """Get breadth/depth stats of XML file (simple analysis)."""
    d = read_xml_file(file_path)
    if "error" in d: return str(d)
    
    def _depth(d):
        if hasattr(d, "keys"):
            return 1 + max([_depth(d[k]) for k in d], default=0)
        return 0
    
    return f"Approx depth: {_depth(d)}"

def validate_well_formed(file_path: str) -> bool:
    d = read_xml_file(file_path)
    return "error" not in d

def write_xml_file(file_path: str, data: Dict[str, Any]) -> str:
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(xmltodict.unparse(data))
        return f"Written to {file_path}"
    except Exception as e:
        return f"Error: {e}"

def write_xml_file_pretty(file_path: str, data: Dict[str, Any]) -> str:
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(xmltodict.unparse(data, pretty=True))
        return f"Written pretty to {file_path}"
    except Exception as e:
        return f"Error: {e}"

# ====================
# Stream Ops (Streaming read)
# ====================
def stream_xml_items(file_path: str, item_depth: int = 2) -> List[Dict[str, Any]]:
    """Stream specific tag from file (generator simulation via `item_depth`).
    xmltodict.parse(generator=True, item_depth=N) returns generator.
    We convert to list for return, hoping it fits in memory (batching for MCP).
    """
    items = []
    try:
        with open(file_path, 'rb') as f:
            # item_depth 2 basically means skipping root and yielding children
            # Use item_callback to collect? Or simple iteration if generator works.
            def _cb(_, item):
                items.append(item)
                return True 
                
            xmltodict.parse(f, item_depth=item_depth, item_callback=_cb)
    except Exception as e:
        items.append({"error": str(e)})
    return items[:1000] # Limit return size

def count_tags_stream(file_path: str, item_depth: int = 2) -> int:
    count = 0
    try:
        with open(file_path, 'rb') as f:
            def _cb(_, item):
                nonlocal count
                count += 1
                return True
            xmltodict.parse(f, item_depth=item_depth, item_callback=_cb)
    except:
        pass
    return count

def extract_tags_stream(file_path: str, tag_name: str, item_depth: int = 2) -> List[Dict[str, Any]]:
    """Extract list of specific tags (e.g. all 'product')."""
    items = []
    try:
        with open(file_path, 'rb') as f:
            def _cb(path, item):
                # path is list of tuples (tag, attrs)
                if path[-1][0] == tag_name:
                    items.append(item)
                return True
            xmltodict.parse(f, item_depth=item_depth, item_callback=_cb)
    except Exception as e:
        return [{"error": str(e)}]
    return items[:500]

def filter_xml_stream(file_path: str, key: str, value: str, item_depth: int = 2) -> List[Dict[str, Any]]:
    """Filter items matching criteria."""
    items = []
    try:
        with open(file_path, 'rb') as f:
            def _cb(_, item):
                # Check if item has key=value (simple check)
                if isinstance(item, dict) and str(item.get(key)) == value:
                    items.append(item)
                return True
            xmltodict.parse(f, item_depth=item_depth, item_callback=_cb)
    except:
        pass
    return items

def stream_to_jsonl(file_path: str, output_path: str, item_depth: int = 2) -> str:
    """Convert large XML to JSONL (one line per item)."""
    count = 0
    try:
        with open(file_path, 'rb') as f_in, open(output_path, 'w', encoding='utf-8') as f_out:
            def _cb(_, item):
                nonlocal count
                f_out.write(json.dumps(item) + "\n")
                count += 1
                return True
            xmltodict.parse(f_in, item_depth=item_depth, item_callback=_cb)
        return f"Converted {count} items to {output_path}"
    except Exception as e:
        return f"Error: {e}"

def sample_xml_stream(file_path: str, limit: int = 100000, item_depth: int = 2) -> List[Dict[str, Any]]:
    items = []
    try:
        with open(file_path, 'rb') as f:
            def _cb(_, item):
                if len(items) < limit:
                    items.append(item)
                    return True
                return False # Stop parsing
            xmltodict.parse(f, item_depth=item_depth, item_callback=_cb)
    except:
        pass
    return items
