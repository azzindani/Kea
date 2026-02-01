
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
from tools import (
    core_ops, parse_ops, walk_ops, serialize_ops, filter_ops, bulk_ops, super_ops
)
import structlog
from typing import Dict, Any, List, Optional

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("html5lib_server")

# ==========================================
# 1. Parsing
# ==========================================
@mcp.tool()
def parse_string(html_input: str) -> str: return parse_ops.parse_string(html_input)
@mcp.tool()
def parse_fragment(html_input: str) -> str: return parse_ops.parse_fragment(html_input)
@mcp.tool()
def parse_lxml(html_input: str) -> str: return parse_ops.parse_lxml(html_input)
@mcp.tool()
def parse_dom(html_input: str) -> str: return parse_ops.parse_dom(html_input)
@mcp.tool()
def parse_validating(html_input: str) -> str: return parse_ops.parse_validating(html_input)
@mcp.tool()
def parse_file(file_path: str) -> str: return parse_ops.parse_file(file_path)
@mcp.tool()
def parser_errors(html_input: str) -> List[str]: return parse_ops.parser_errors(html_input)
@mcp.tool()
def detect_encoding(file_path: str) -> str: return parse_ops.detect_encoding(file_path)

# ==========================================
# 2. Walk
# ==========================================
@mcp.tool()
def walk_tree_print(html_input: str) -> str: return walk_ops.walk_tree_print(html_input)
@mcp.tool()
def walk_get_tokens(html_input: str, limit: int = 100000) -> List[Dict[str, Any]]: return walk_ops.walk_get_tokens(html_input, limit)
@mcp.tool()
def walk_find_tags(html_input: str, tag_name: str) -> List[str]: return walk_ops.walk_find_tags(html_input, tag_name)
@mcp.tool()
def walk_extract_text(html_input: str) -> str: return walk_ops.walk_extract_text(html_input)
@mcp.tool()
def count_tokens(html_input: str) -> Dict[str, int]: return walk_ops.count_tokens(html_input)
@mcp.tool()
def lint_stream(html_input: str) -> str: return walk_ops.lint_stream(html_input)

# ==========================================
# 3. Serialize
# ==========================================
@mcp.tool()
def serialize_tree(html_input: str) -> str: return serialize_ops.serialize_tree(html_input)
@mcp.tool()
def serialize_minidom(html_input: str) -> str: return serialize_ops.serialize_minidom(html_input)
@mcp.tool()
def serialize_pretty(html_input: str) -> str: return serialize_ops.serialize_pretty(html_input)
@mcp.tool()
def serialize_no_whitespace(html_input: str) -> str: return serialize_ops.serialize_no_whitespace(html_input)
@mcp.tool()
def serialize_inject_meta(html_input: str) -> str: return serialize_ops.serialize_inject_meta(html_input)
@mcp.tool()
def reencode_html(html_input: str, encoding: str) -> str: return serialize_ops.reencode_html(html_input, encoding)

# ==========================================
# 4. Filter
# ==========================================
@mcp.tool()
def sanitize_html(html_input: str) -> str: return filter_ops.sanitize_html(html_input)
@mcp.tool()
def filter_whitespace(html_input: str) -> str: return filter_ops.filter_whitespace(html_input)
@mcp.tool()
def filter_optional_tags(html_input: str) -> str: return filter_ops.filter_optional_tags(html_input)
@mcp.tool()
def filter_comments(html_input: str) -> str: return filter_ops.filter_comments(html_input)
@mcp.tool()
def filter_inject_token(html_input: str, token_type: str, name: str) -> str: return filter_ops.filter_inject_token(html_input, token_type, name)
@mcp.tool()
def escape_html_entities(text: str) -> str: return filter_ops.escape_html_entities(text)
@mcp.tool()
def alphabetical_attributes(html_input: str) -> str: return filter_ops.alphabetical_attributes(html_input)

# ==========================================
# 5. Bulk
# ==========================================
@mcp.tool()
def bulk_parse_validate(directory: str) -> Dict[str, str]: return bulk_ops.bulk_parse_validate(directory)
@mcp.tool()
def bulk_sanitize_dir(directory: str, output_dir: str) -> str: return bulk_ops.bulk_sanitize_dir(directory, output_dir)
@mcp.tool()
def bulk_extract_text(directory: str) -> Dict[str, str]: return bulk_ops.bulk_extract_text(directory)
@mcp.tool()
def bulk_convert_encoding(directory: str, target_encoding: str = "utf-8") -> str: return bulk_ops.bulk_convert_encoding(directory, target_encoding)
@mcp.tool()
def grep_html_tokens(directory: str, token_name: str) -> Dict[str, int]: return bulk_ops.grep_html_tokens(directory, token_name)
@mcp.tool()
def parse_benchmarks(file_size_mb: int = 1) -> str: return bulk_ops.parse_benchmarks(file_size_mb)

# ==========================================
# 6. Super
# ==========================================
@mcp.tool()
def repair_html_page(html_input: str) -> str: return super_ops.repair_html_page(html_input)
@mcp.tool()
def html_diff_token(html_a: str, html_b: str) -> str: return super_ops.html_diff_token(html_a, html_b)
@mcp.tool()
def table_extractor_resilient(html_input: str) -> str: return super_ops.table_extractor_resilient(html_input)
@mcp.tool()
def visualize_dom_tree(html_input: str) -> str: return super_ops.visualize_dom_tree(html_input)
@mcp.tool()
def extract_links_stream(html_input: str) -> List[str]: return super_ops.extract_links_stream(html_input)
@mcp.tool()
def convert_html_to_valid_xml(html_input: str) -> str: return super_ops.convert_html_to_valid_xml(html_input)
@mcp.tool()
def tree_adapter_bridge(html_input: str, target: str = 'dom') -> str: return super_ops.tree_adapter_bridge(html_input, target)
@mcp.tool()
def inspect_treebuilder_options() -> List[str]: return super_ops.inspect_treebuilder_options()
@mcp.tool()
def memory_usage_estimate(html_input: str) -> str: return super_ops.memory_usage_estimate(html_input)
@mcp.tool()
def profile_page_structure(html_input: str) -> str: return super_ops.profile_page_structure(html_input)
@mcp.tool()
def find_broken_links_dummy(html_input: str) -> str: return super_ops.find_broken_links_dummy(html_input)
@mcp.tool()
def generate_toc_from_html(html_input: str) -> str: return super_ops.generate_toc_from_html(html_input)
@mcp.tool()
def html_minify_aggressive(html_input: str) -> str: return super_ops.html_minify_aggressive(html_input)
@mcp.tool()
def extract_metadata(html_input: str) -> Dict[str, str]: return super_ops.extract_metadata(html_input)
@mcp.tool()
def inject_script_tag(html_input: str, script_src: str) -> str: return super_ops.inject_script_tag(html_input, script_src)
@mcp.tool()
def remove_elements_by_class(html_input: str, class_name: str) -> str: return super_ops.remove_elements_by_class(html_input, class_name)
@mcp.tool()
def highlight_text(html_input: str, text: str) -> str: return super_ops.highlight_text(html_input, text)
@mcp.tool()
def auto_close_tags(html_input: str) -> str: return super_ops.auto_close_tags(html_input)
@mcp.tool()
def simulate_browser_parse(html_input: str) -> str: return super_ops.simulate_browser_parse(html_input)
@mcp.tool()
def stream_to_json(html_input: str) -> str: return super_ops.stream_to_json(html_input)
@mcp.tool()
def debug_encoding_sniff(bytes_input: bytes) -> str: return "Requires bytes"
@mcp.tool()
def merge_html_fragments(fragments: List[str]) -> str: return super_ops.merge_html_fragments(fragments)
@mcp.tool()
def split_html_sections(html_input: str) -> List[str]: return super_ops.split_html_sections(html_input)
@mcp.tool()
def validate_doctype(html_input: str) -> str: return super_ops.validate_doctype(html_input)
@mcp.tool()
def html5_conformance_check(html_input: str) -> str: return super_ops.html5_conformance_check(html_input)
@mcp.tool()
def anonymize_text_content(html_input: str) -> str: return super_ops.anonymize_text_content(html_input)

if __name__ == "__main__":
    mcp.run()