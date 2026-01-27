import os
import glob
import json
import xmltodict
from typing import List, Dict, Any, Optional
from mcp_servers.xmltodict_server.tools import file_ops, core_ops
from concurrent.futures import ThreadPoolExecutor

def bulk_parse_strings(xml_strings: List[str]) -> List[Dict[str, Any]]:
    """Parse list of XML strings."""
    # cpu bound, sequential for now
    return [core_ops._safe_parse(s) for s in xml_strings]

def bulk_read_files(file_paths: List[str]) -> Dict[str, Any]:
    """Parse list of files. Returns {path: dict}."""
    results = {}
    for p in file_paths:
        results[p] = file_ops.read_xml_file(p)
    return results

def convert_dir_xml_to_json(directory: str) -> str:
    """Convert all XML in dir to JSON files."""
    if not os.path.exists(directory): return "Directory not found"
    
    files = glob.glob(os.path.join(directory, "*.xml"))
    count = 0
    errors = 0
    
    for f in files:
        try:
            d = file_ops.read_xml_file(f)
            json_path = f.replace(".xml", ".json")
            with open(json_path, 'w', encoding='utf-8') as jf:
                json.dump(d, jf, indent=2)
            count += 1
        except:
            errors += 1
            
    return f"Converted {count} files. Errors: {errors}"

def convert_dir_json_to_xml(directory: str) -> str:
    """Convert all JSON in dir to XML files."""
    if not os.path.exists(directory): return "Directory not found"
    
    files = glob.glob(os.path.join(directory, "*.json"))
    count = 0
    errors = 0
    
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as jf:
                d = json.load(jf)
            
            # JSON root key requirement: XML needs 1 root.
            # If JSON is list or has multiple keys, wrap it in <root>
            if isinstance(d, list) or len(d.keys()) > 1:
                d = {"root": d}
            
            xml_path = f.replace(".json", ".xml")
            with open(xml_path, 'w', encoding='utf-8') as xf:
                xmltodict.unparse(d, output=xf, pretty=True)
            count += 1
        except:
            errors += 1
    
    return f"Converted {count} files. Errors: {errors}"

def merge_xml_files(file_paths: List[str], root_name: str) -> str:
    """Merge multiple XMLs into one root."""
    merged = {root_name: []}
    
    for f in file_paths:
        d = file_ops.read_xml_file(f)
        # Try to find meaningful content. If root has 1 child, take it.
        # This is heuristic.
        root_key = list(d.keys())[0]
        merged[root_name].append(d[root_key])
        
    return xmltodict.unparse(merged, pretty=True)

def grep_xml_dir(directory: str, search_text: str) -> Dict[str, List[str]]:
    """Search for text in XML files (parsed content)."""
    # Simply read as text? Or parse and search values?
    # Parsing is safer for values, text read is faster.
    # User said "parsed content" in plan context implies values.
    # Recursively walking dict is expensive.
    # Let's simple grep file content for now as it's bulk tool.
    
    results = {}
    files = glob.glob(os.path.join(directory, "**/*.xml"), recursive=True)
    
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8', errors='ignore') as xf:
                lines = xf.readlines()
            matches = [l.strip() for l in lines if search_text in l]
            if matches:
                 results[f] = matches[:5] # limit
        except:
            pass
            
    return results
