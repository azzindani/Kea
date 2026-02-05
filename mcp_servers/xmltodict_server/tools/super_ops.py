import json
import xmltodict
import os
import csv
from typing import Dict, Any, List, Optional
from mcp_servers.xmltodict_server.tools import file_ops, core_ops, unparse_ops
import re

def xml_to_json_file(xml_file: str, json_file: str) -> str:
    """Full file conversion."""
    d = file_ops.read_xml_file(xml_file)
    if "error" in d: return str(d)
    try:
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(d, f, indent=2)
        return f"Converted {xml_file} to {json_file}"
    except Exception as e:
        return f"Error: {e}"

def json_to_xml_file(json_file: str, xml_file: str) -> str:
    """Full file conversion."""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            d = json.load(f)
        # Ensure single root
        if len(d) != 1: d = {"root": d}
        file_ops.write_xml_file_pretty(xml_file, d)
        return f"Converted {json_file} to {xml_file}"
    except Exception as e:
        return f"Error: {e}"

def diff_xml_files(file_a: str, file_b: str) -> str:
    """Compare two XML files (logic: dict diff via json dump equality check or set)."""
    da = file_ops.read_xml_file(file_a)
    db = file_ops.read_xml_file(file_b)
    
    # Simple strict equality
    import json
    ja = json.dumps(da, sort_keys=True)
    jb = json.dumps(db, sort_keys=True)
    
    if ja == jb: return "Files are structurally identical."
    
    # Length diff
    return f"Files differ. Size A: {len(ja)} chars, Size B: {len(jb)} chars."

def flatten_xml(file_path: str) -> Dict[str, Any]:
    """Flatten nested XML to single depth dict (dot notation)."""
    d = file_ops.read_xml_file(file_path)
    if "error" in d: return d
    
    flat = {}
    def _recruit(prefix, val):
        if isinstance(val, dict):
            for k, v in val.items():
                _recruit(f"{prefix}.{k}" if prefix else k, v)
        elif isinstance(val, list):
            for i, v in enumerate(val):
                _recruit(f"{prefix}[{i}]", v)
        else:
            flat[prefix] = val
            
    _recruit("", d)
    return flat

def search_xml_path(file_path: str, path: str) -> Any:
    """Get value at path `root.child.item`."""
    d = file_ops.read_xml_file(file_path)
    keys = path.split('.')
    curr = d
    try:
        for k in keys:
            if isinstance(curr, list):
                # Handle array index if k is int
                if k.isdigit():
                    curr = curr[int(k)]
                else:
                    return None
            else:
                curr = curr[k]
        return curr
    except:
        return None

def mask_xml_sensitive(file_path: str, keys: List[str]) -> str:
    """Redact keys in XML file."""
    d = file_ops.read_xml_file(file_path)
    
    def _mask(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in keys:
                    obj[k] = "***REDACTED***"
                else:
                    _mask(v)
        elif isinstance(obj, list):
            for v in obj:
                _mask(v)
                
    _mask(d)
    return xmltodict.unparse(d, pretty=True)

def xml_to_csv_table(file_path: str, csv_path: str, item_key: str) -> str:
    """Convert uniform list of XML items to CSV.
    Assumes XML structure like <root><item_key>...</item_key><item_key>...</item_key></root>
    """
    d = file_ops.read_xml_file(file_path)
    try:
        # Navigate to list. Heuristic: Find the list of dicts.
        # Or look for item_key in root.
        root = list(d.values())[0]
        items = root.get(item_key)
        
        if not items: return "Item key not found"
        if not isinstance(items, list): items = [items]
        
        # Collect headers
        headers = set()
        for i in items:
            headers.update(i.keys())
        headers = sorted(list(headers))
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for i in items:
                # Filter keys not in headers (nested objects stringified)
                row = {k: str(v) for k, v in i.items() if k in headers}
                writer.writerow(row)
                
        return f"Converted to {csv_path}"
    except Exception as e:
        return f"Error: {e}"

def reformat_xml_file(file_path: str) -> str:
    """Read and write back Pretty."""
    d = file_ops.read_xml_file(file_path)
    if "error" in d: return str(d)
    return file_ops.write_xml_file_pretty(file_path, d)

def sanitize_xml_tags(file_path: str) -> str:
    """Lowercase/slugify keys."""
    d = file_ops.read_xml_file(file_path)
    
    def _sanitize(obj):
        if isinstance(obj, dict):
            new_obj = {}
            for k, v in obj.items():
                new_k = k.lower().replace(' ', '_')
                new_obj[new_k] = _sanitize(v)
            return new_obj
        elif isinstance(obj, list):
            return [_sanitize(i) for i in obj]
        else:
            return obj
            
    sanitized = _sanitize(d)
    return xmltodict.unparse(sanitized, pretty=True)

def generate_xsd_inference(file_path: str) -> str:
    """Infer XSD/Structure from XML (mockup)."""
    # Real XSD inference is hard. We'll return a structure summary.
    flat = flatten_xml(file_path)
    types = {}
    for k, v in flat.items():
        base_k = re.sub(r'\[\d+\]', '', k) # Remove indices
        t = type(v).__name__
        if base_k not in types: types[base_k] = set()
        types[base_k].add(t)
        
    report = "Inferred Structure:\n"
    for k, v in types.items():
        report += f"{k}: {', '.join(v)}\n"
    return report

def xml_heatmap(file_path: str) -> str:
    """Text visualization of depth/complexity."""
    # Count tags at each depth
    d = file_ops.read_xml_file(file_path)
    depth_counts = {}
    
    def _traverse(obj, depth):
        depth_counts[depth] = depth_counts.get(depth, 0) + 1
        if isinstance(obj, dict):
            for v in obj.values(): _traverse(v, depth+1)
        elif isinstance(obj, list):
            for v in obj: _traverse(v, depth)
            
    _traverse(d, 0)
    
    viz = ""
    for depth, count in sorted(depth_counts.items()):
        bar = "#" * min(50, count)
        viz += f"Depth {depth}: {count} {bar}\n"
    return viz
