
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "mcp",
#   "structlog",
# ]
# ///

from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.html5lib_server.tools import (
    core_ops, parse_ops, walk_ops, serialize_ops, filter_ops, bulk_ops, super_ops
)
import structlog
from typing import Dict, Any, List, Optional

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging import setup_logging
setup_logging()

mcp = FastMCP("html5lib_server")

# ==========================================
# 1. Parsing
# ==========================================
# ==========================================
# 1. Parsing
# ==========================================
@mcp.tool()
def parse_string(html_input: str) -> str: 
    """PARSES HTML string. [ACTION]
    
    [RAG Context]
    """
    return parse_ops.parse_string(html_input)

@mcp.tool()
def parse_fragment(html_input: str) -> str: 
    """PARSES HTML fragment. [ACTION]
    
    [RAG Context]
    """
    return parse_ops.parse_fragment(html_input)

@mcp.tool()
def parse_lxml(html_input: str) -> str: 
    """PARSES HTML using lxml. [ACTION]
    
    [RAG Context]
    """
    return parse_ops.parse_lxml(html_input)

@mcp.tool()
def parse_dom(html_input: str) -> str: 
    """PARSES HTML to DOM. [ACTION]
    
    [RAG Context]
    Using xml.dom.minidom.
    """
    return parse_ops.parse_dom(html_input)

@mcp.tool()
def parse_validating(html_input: str) -> str: 
    """PARSES HTML with validation. [ACTION]
    
    [RAG Context]
    """
    return parse_ops.parse_validating(html_input)

@mcp.tool()
def parse_file(file_path: str) -> str: 
    """PARSES HTML file. [DATA]
    
    [RAG Context]
    Returns tree string.
    """
    return parse_ops.parse_file(file_path)

@mcp.tool()
def parser_errors(html_input: str) -> List[str]: 
    """GETS parsing errors. [DATA]
    
    [RAG Context]
    Detailed error list.
    """
    return parse_ops.parser_errors(html_input)

@mcp.tool()
def detect_encoding(file_path: str) -> str: 
    """DETECTS file encoding. [DATA]
    
    [RAG Context]
    """
    return parse_ops.detect_encoding(file_path)

# ==========================================
# 2. Walk
# ==========================================
@mcp.tool()
def walk_tree_print(html_input: str) -> str: 
    """PRINTS DOM tree. [DATA]
    
    [RAG Context]
    Visual tree.
    """
    return walk_ops.walk_tree_print(html_input)

@mcp.tool()
def walk_get_tokens(html_input: str, limit: int = 100000) -> List[Dict[str, Any]]: 
    """GETS token list. [DATA]
    
    [RAG Context]
    """
    return walk_ops.walk_get_tokens(html_input, limit)

@mcp.tool()
def walk_find_tags(html_input: str, tag_name: str) -> List[str]: 
    """FINDS tags in tree. [DATA]
    
    [RAG Context]
    """
    return walk_ops.walk_find_tags(html_input, tag_name)

@mcp.tool()
def walk_extract_text(html_input: str) -> str: 
    """EXTRACTS text from tree. [DATA]
    
    [RAG Context]
    """
    return walk_ops.walk_extract_text(html_input)

@mcp.tool()
def count_tokens(html_input: str) -> Dict[str, int]: 
    """COUNTS tokens. [DATA]
    
    [RAG Context]
    START, END, CHAR, etc.
    """
    return walk_ops.count_tokens(html_input)

@mcp.tool()
def lint_stream(html_input: str) -> str: 
    """LINTS HTML stream. [DATA]
    
    [RAG Context]
    Checks for errors.
    """
    return walk_ops.lint_stream(html_input)

# ==========================================
# 3. Serialize
# ==========================================
@mcp.tool()
def serialize_tree(html_input: str) -> str: 
    """SERIALIZES tree to HTML. [ACTION]
    
    [RAG Context]
    """
    return serialize_ops.serialize_tree(html_input)

@mcp.tool()
def serialize_minidom(html_input: str) -> str: 
    """SERIALIZES DOM to HTML. [ACTION]
    
    [RAG Context]
    """
    return serialize_ops.serialize_minidom(html_input)

@mcp.tool()
def serialize_pretty(html_input: str) -> str: 
    """SERIALIZES pretty HTML. [ACTION]
    
    [RAG Context]
    """
    return serialize_ops.serialize_pretty(html_input)

@mcp.tool()
def serialize_no_whitespace(html_input: str) -> str: 
    """SERIALIZES compact HTML. [ACTION]
    
    [RAG Context]
    """
    return serialize_ops.serialize_no_whitespace(html_input)

@mcp.tool()
def serialize_inject_meta(html_input: str) -> str: 
    """INJECTS meta charset. [ACTION]
    
    [RAG Context]
    """
    return serialize_ops.serialize_inject_meta(html_input)

@mcp.tool()
def reencode_html(html_input: str, encoding: str) -> str: 
    """REENCODES HTML. [ACTION]
    
    [RAG Context]
    """
    return serialize_ops.reencode_html(html_input, encoding)

# ==========================================
# 4. Filter
# ==========================================
@mcp.tool()
def sanitize_html(html_input: str) -> str: 
    """SANITIZES HTML. [ACTION]
    
    [RAG Context]
    Removes dangerous tags.
    """
    return filter_ops.sanitize_html(html_input)

@mcp.tool()
def filter_whitespace(html_input: str) -> str: 
    """REMOVES whitespace. [ACTION]
    
    [RAG Context]
    """
    return filter_ops.filter_whitespace(html_input)

@mcp.tool()
def filter_optional_tags(html_input: str) -> str: 
    """REMOVES optional tags. [ACTION]
    
    [RAG Context]
    html, head, body, etc.
    """
    return filter_ops.filter_optional_tags(html_input)

@mcp.tool()
def filter_comments(html_input: str) -> str: 
    """REMOVES comments. [ACTION]
    
    [RAG Context]
    """
    return filter_ops.filter_comments(html_input)

@mcp.tool()
def filter_inject_token(html_input: str, token_type: str, name: str) -> str: 
    """INJECTS token. [ACTION]
    
    [RAG Context]
    Low-level injection.
    """
    return filter_ops.filter_inject_token(html_input, token_type, name)

@mcp.tool()
def escape_html_entities(text: str) -> str: 
    """ESCAPES entities. [ACTION]
    
    [RAG Context]
    """
    return filter_ops.escape_html_entities(text)

@mcp.tool()
def alphabetical_attributes(html_input: str) -> str: 
    """SORTS attributes. [ACTION]
    
    [RAG Context]
    """
    return filter_ops.alphabetical_attributes(html_input)

# ==========================================
# 5. Bulk
# ==========================================
# ==========================================
# 5. Bulk
# ==========================================
@mcp.tool()
def bulk_parse_validate(directory: str) -> Dict[str, str]: 
    """PARSES and validates directory. [ACTION]
    
    [RAG Context]
    """
    return bulk_ops.bulk_parse_validate(directory)

@mcp.tool()
def bulk_sanitize_dir(directory: str, output_dir: str) -> str: 
    """SANITIZES entire directory. [ACTION]
    
    [RAG Context]
    """
    return bulk_ops.bulk_sanitize_dir(directory, output_dir)

@mcp.tool()
def bulk_extract_text(directory: str) -> Dict[str, str]: 
    """EXTRACTS text from directory. [DATA]
    
    [RAG Context]
    """
    return bulk_ops.bulk_extract_text(directory)

@mcp.tool()
def bulk_convert_encoding(directory: str, target_encoding: str = "utf-8") -> str: 
    """CONVERTS encoding in directory. [ACTION]
    
    [RAG Context]
    """
    return bulk_ops.bulk_convert_encoding(directory, target_encoding)

@mcp.tool()
def grep_html_tokens(directory: str, token_name: str) -> Dict[str, int]: 
    """COUNTS tokens in directory. [DATA]
    
    [RAG Context]
    """
    return bulk_ops.grep_html_tokens(directory, token_name)

@mcp.tool()
def parse_benchmarks(file_size_mb: int = 1) -> str: 
    """RUNS parsing benchmarks. [DATA]
    
    [RAG Context]
    """
    return bulk_ops.parse_benchmarks(file_size_mb)

# ==========================================
# 6. Super
# ==========================================
@mcp.tool()
def repair_html_page(html_input: str) -> str: 
    """REPAIRS broken HTML. [ACTION]
    
    [RAG Context]
    """
    return super_ops.repair_html_page(html_input)

@mcp.tool()
def html_diff_token(html_a: str, html_b: str) -> str: 
    """DIFFS HTML by token. [DATA]
    
    [RAG Context]
    """
    return super_ops.html_diff_token(html_a, html_b)

@mcp.tool()
def table_extractor_resilient(html_input: str) -> str: 
    """EXTRACTS broken tables. [DATA]
    
    [RAG Context]
    """
    return super_ops.table_extractor_resilient(html_input)

@mcp.tool()
def visualize_dom_tree(html_input: str) -> str: 
    """VISUALIZES DOM with graphviz. [DATA]
    
    [RAG Context]
    """
    return super_ops.visualize_dom_tree(html_input)

@mcp.tool()
def extract_links_stream(html_input: str) -> List[str]: 
    """EXTRACTS links (streaming). [DATA]
    
    [RAG Context]
    """
    return super_ops.extract_links_stream(html_input)

@mcp.tool()
def convert_html_to_valid_xml(html_input: str) -> str: 
    """CONVERTS HTML to XML (XHTML). [ACTION]
    
    [RAG Context]
    """
    return super_ops.convert_html_to_valid_xml(html_input)

@mcp.tool()
def tree_adapter_bridge(html_input: str, target: str = 'dom') -> str: 
    """BRIDGES tree adapters. [ACTION]
    
    [RAG Context]
    """
    return super_ops.tree_adapter_bridge(html_input, target)

@mcp.tool()
def inspect_treebuilder_options() -> List[str]: 
    """LISTS builder options. [DATA]
    
    [RAG Context]
    """
    return super_ops.inspect_treebuilder_options()

@mcp.tool()
def memory_usage_estimate(html_input: str) -> str: 
    """ESTIMATES memory usage. [DATA]
    
    [RAG Context]
    """
    return super_ops.memory_usage_estimate(html_input)

@mcp.tool()
def profile_page_structure(html_input: str) -> str: 
    """PROFILES page metrics. [DATA]
    
    [RAG Context]
    """
    return super_ops.profile_page_structure(html_input)

@mcp.tool()
def generate_toc_from_html(html_input: str) -> str: 
    """GENERATES table of contents. [DATA]
    
    [RAG Context]
    """
    return super_ops.generate_toc_from_html(html_input)

@mcp.tool()
def html_minify_aggressive(html_input: str) -> str: 
    """MINIFIES HTML aggressively. [ACTION]
    
    [RAG Context]
    """
    return super_ops.html_minify_aggressive(html_input)

@mcp.tool()
def extract_metadata(html_input: str) -> Dict[str, str]: 
    """EXTRACTS all metadata. [DATA]
    
    [RAG Context]
    """
    return super_ops.extract_metadata(html_input)

@mcp.tool()
def inject_script_tag(html_input: str, script_src: str) -> str: 
    """INJECTS script tag. [ACTION]
    
    [RAG Context]
    """
    return super_ops.inject_script_tag(html_input, script_src)

@mcp.tool()
def remove_elements_by_class(html_input: str, class_name: str) -> str: 
    """REMOVES elements by class. [ACTION]
    
    [RAG Context]
    """
    return super_ops.remove_elements_by_class(html_input, class_name)

@mcp.tool()
def highlight_text(html_input: str, text: str) -> str: 
    """HIGHLIGHTS text matches. [ACTION]
    
    [RAG Context]
    """
    return super_ops.highlight_text(html_input, text)

@mcp.tool()
def auto_close_tags(html_input: str) -> str: 
    """CLOSES unclosed tags. [ACTION]
    
    [RAG Context]
    """
    return super_ops.auto_close_tags(html_input)

@mcp.tool()
def simulate_browser_parse(html_input: str) -> str: 
    """SIMULATES browser parsing. [DATA]
    
    [RAG Context]
    """
    return super_ops.simulate_browser_parse(html_input)

@mcp.tool()
def stream_to_json(html_input: str) -> str: 
    """CONVERTS stream to JSON. [DATA]
    
    [RAG Context]
    """
    return super_ops.stream_to_json(html_input)

@mcp.tool()
def debug_encoding_sniff(bytes_input: bytes) -> str: 
    """SNIFFS encoding (debug). [DATA]
    
    [RAG Context]
    """
    return "Requires bytes"

@mcp.tool()
def merge_html_fragments(fragments: List[str]) -> str: 
    """MERGES HTML fragments. [ACTION]
    
    [RAG Context]
    """
    return super_ops.merge_html_fragments(fragments)

@mcp.tool()
def split_html_sections(html_input: str) -> List[str]: 
    """SPLITS HTML by headers. [DATA]
    
    [RAG Context]
    """
    return super_ops.split_html_sections(html_input)

@mcp.tool()
def validate_doctype(html_input: str) -> str: 
    """VALIDATES doctype. [DATA]
    
    [RAG Context]
    """
    return super_ops.validate_doctype(html_input)

@mcp.tool()
def html5_conformance_check(html_input: str) -> str: 
    """CHECKS HTML5 rules. [DATA]
    
    [RAG Context]
    """
    return super_ops.html5_conformance_check(html_input)

@mcp.tool()
def anonymize_text_content(html_input: str) -> str: 
    """ANONYMIZES content. [ACTION]
    
    [RAG Context]
    """
    return super_ops.anonymize_text_content(html_input)

if __name__ == "__main__":
    mcp.run()