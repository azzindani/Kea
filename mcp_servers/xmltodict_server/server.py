# /// script
# dependencies = [
#   "mcp",
#   "structlog",
# ]
# ///

from mcp.server.fastmcp import FastMCP
from mcp_servers.xmltodict_server.tools import (
    core_ops, parse_ops, unparse_ops, file_ops, bulk_ops, super_ops
)
import structlog
from typing import Dict, Any, List, Optional

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("xmltodict_server")

# ==========================================
# 1. Parsing
# ==========================================
@mcp.tool()
def parse_xml_string(xml_input: str) -> Dict[str, Any]: return parse_ops.parse_xml_string(xml_input)
@mcp.tool()
def parse_xml_no_attrs(xml_input: str) -> Dict[str, Any]: return parse_ops.parse_xml_no_attrs(xml_input)
@mcp.tool()
def parse_xml_no_namespaces(xml_input: str) -> Dict[str, Any]: return parse_ops.parse_xml_no_namespaces(xml_input)
@mcp.tool()
def parse_xml_force_list(xml_input: str, tags: List[str]) -> Dict[str, Any]: return parse_ops.parse_xml_force_list(xml_input, tags)
@mcp.tool()
def parse_xml_force_cdata(xml_input: str) -> Dict[str, Any]: return parse_ops.parse_xml_force_cdata(xml_input)
@mcp.tool()
def parse_xml_custom_encoding(xml_input: str, encoding: str) -> Dict[str, Any]: return parse_ops.parse_xml_custom_encoding(xml_input, encoding)
@mcp.tool()
def parse_xml_disable_entities(xml_input: str) -> Dict[str, Any]: return parse_ops.parse_xml_disable_entities(xml_input)
@mcp.tool()
def parse_xml_strip_whitespace(xml_input: str) -> Dict[str, Any]: return parse_ops.parse_xml_strip_whitespace(xml_input)
@mcp.tool()
def parse_fragment(xml_fragment: str) -> Dict[str, Any]: return parse_ops.parse_fragment(xml_fragment)
@mcp.tool()
def get_namespaces(xml_input: str) -> Dict[str, str]: return parse_ops.get_namespaces(xml_input)

# ==========================================
# 2. Unparsing
# ==========================================
@mcp.tool()
def unparse_dict_string(data: Dict[str, Any]) -> str: return unparse_ops.unparse_dict_string(data)
@mcp.tool()
def unparse_dict_pretty(data: Dict[str, Any]) -> str: return unparse_ops.unparse_dict_pretty(data)
@mcp.tool()
def unparse_dict_no_header(data: Dict[str, Any]) -> str: return unparse_ops.unparse_dict_no_header(data)
@mcp.tool()
def unparse_dict_full_document(data: Dict[str, Any]) -> str: return unparse_ops.unparse_dict_full_document(data)
@mcp.tool()
def unparse_dict_short_empty(data: Dict[str, Any]) -> str: return unparse_ops.unparse_dict_short_empty(data)
@mcp.tool()
def dict_to_soap_envelope(data: Dict[str, Any]) -> str: return unparse_ops.dict_to_soap_envelope(data)
@mcp.tool()
def dict_to_rss_xml(data: Dict[str, Any]) -> str: return unparse_ops.dict_to_rss_xml(data)
@mcp.tool()
def dict_to_svg_xml(data: Dict[str, Any]) -> str: return unparse_ops.dict_to_svg_xml(data)

# ==========================================
# 3. File Ops & Streaming
# ==========================================
@mcp.tool()
def read_xml_file(file_path: str) -> Dict[str, Any]: return file_ops.read_xml_file(file_path)
@mcp.tool()
def read_xml_file_no_attrs(file_path: str) -> Dict[str, Any]: return file_ops.read_xml_file_no_attrs(file_path)
@mcp.tool()
def read_xml_config(file_path: str) -> Dict[str, Any]: return file_ops.read_xml_config(file_path)
@mcp.tool()
def read_rss_feed(file_path: str) -> Dict[str, Any]: return file_ops.read_rss_feed(file_path)
@mcp.tool()
def read_atom_feed(file_path: str) -> Dict[str, Any]: return file_ops.read_atom_feed(file_path)
@mcp.tool()
def read_svg_file(file_path: str) -> Dict[str, Any]: return file_ops.read_svg_file(file_path)
@mcp.tool()
def scan_xml_structure(file_path: str) -> str: return file_ops.scan_xml_structure(file_path)
@mcp.tool()
def validate_well_formed(file_path: str) -> bool: return file_ops.validate_well_formed(file_path)
@mcp.tool()
def write_xml_file(file_path: str, data: Dict[str, Any]) -> str: return file_ops.write_xml_file(file_path, data)
@mcp.tool()
def write_xml_file_pretty(file_path: str, data: Dict[str, Any]) -> str: return file_ops.write_xml_file_pretty(file_path, data)
@mcp.tool()
def stream_xml_items(file_path: str, item_depth: int = 2) -> List[Dict[str, Any]]: return file_ops.stream_xml_items(file_path, item_depth)
@mcp.tool()
def count_tags_stream(file_path: str, item_depth: int = 2) -> int: return file_ops.count_tags_stream(file_path, item_depth)
@mcp.tool()
def extract_tags_stream(file_path: str, tag_name: str, item_depth: int = 2) -> List[Dict[str, Any]]: return file_ops.extract_tags_stream(file_path, tag_name, item_depth)
@mcp.tool()
def filter_xml_stream(file_path: str, key: str, value: str, item_depth: int = 2) -> List[Dict[str, Any]]: return file_ops.filter_xml_stream(file_path, key, value, item_depth)
@mcp.tool()
def stream_to_jsonl(file_path: str, output_path: str, item_depth: int = 2) -> str: return file_ops.stream_to_jsonl(file_path, output_path, item_depth)
@mcp.tool()
def sample_xml_stream(file_path: str, limit: int = 100000, item_depth: int = 2) -> List[Dict[str, Any]]: return file_ops.sample_xml_stream(file_path, limit, item_depth)

# ==========================================
# 4. Bulk
# ==========================================
@mcp.tool()
def bulk_parse_strings(xml_strings: List[str]) -> List[Dict[str, Any]]: return bulk_ops.bulk_parse_strings(xml_strings)
@mcp.tool()
def bulk_read_files(file_paths: List[str]) -> Dict[str, Any]: return bulk_ops.bulk_read_files(file_paths)
@mcp.tool()
def convert_dir_xml_to_json(directory: str) -> str: return bulk_ops.convert_dir_xml_to_json(directory)
@mcp.tool()
def convert_dir_json_to_xml(directory: str) -> str: return bulk_ops.convert_dir_json_to_xml(directory)
@mcp.tool()
def merge_xml_files(file_paths: List[str], root_name: str) -> str: return bulk_ops.merge_xml_files(file_paths, root_name)
@mcp.tool()
def grep_xml_dir(directory: str, search_text: str) -> Dict[str, List[str]]: return bulk_ops.grep_xml_dir(directory, search_text)

# ==========================================
# 5. Super
# ==========================================
@mcp.tool()
def xml_to_json_file(xml_file: str, json_file: str) -> str: return super_ops.xml_to_json_file(xml_file, json_file)
@mcp.tool()
def json_to_xml_file(json_file: str, xml_file: str) -> str: return super_ops.json_to_xml_file(json_file, xml_file)
@mcp.tool()
def diff_xml_files(file_a: str, file_b: str) -> str: return super_ops.diff_xml_files(file_a, file_b)
@mcp.tool()
def flatten_xml(file_path: str) -> Dict[str, Any]: return super_ops.flatten_xml(file_path)
@mcp.tool()
def search_xml_path(file_path: str, path: str) -> Any: return super_ops.search_xml_path(file_path, path)
@mcp.tool()
def mask_xml_sensitive(file_path: str, keys: List[str]) -> str: return super_ops.mask_xml_sensitive(file_path, keys)
@mcp.tool()
def xml_to_csv_table(file_path: str, csv_path: str, item_key: str) -> str: return super_ops.xml_to_csv_table(file_path, csv_path, item_key)
@mcp.tool()
def reformat_xml_file(file_path: str) -> str: return super_ops.reformat_xml_file(file_path)
@mcp.tool()
def sanitize_xml_tags(file_path: str) -> str: return super_ops.sanitize_xml_tags(file_path)
@mcp.tool()
def generate_xsd_inference(file_path: str) -> str: return super_ops.generate_xsd_inference(file_path)
@mcp.tool()
def xml_heatmap(file_path: str) -> str: return super_ops.xml_heatmap(file_path)

if __name__ == "__main__":
    mcp.run()
