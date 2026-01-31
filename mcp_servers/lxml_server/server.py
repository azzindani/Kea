# /// script
# dependencies = [
#   "mcp",
#   "structlog",
# ]
# ///

from mcp.server.fastmcp import FastMCP
from mcp_servers.lxml_server.tools import (
    core_ops, xpath_ops, transform_ops, validate_ops, objectify_ops, bulk_ops, super_ops
)
import structlog
from typing import Dict, Any, List, Optional

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("lxml_server")

# ==========================================
# 1. Core
# ==========================================
@mcp.tool()
def parse_xml_string(xml_input: str) -> str: return core_ops.parse_xml_string(xml_input)
@mcp.tool()
def parse_html_string(html_input: str) -> str: return core_ops.parse_html_string(html_input)
@mcp.tool()
def parse_file(file_path: str) -> str: return core_ops.parse_file(file_path)
@mcp.tool()
def parse_xml_recover(xml_input: str) -> str: return core_ops.parse_xml_recover(xml_input)
@mcp.tool()
def to_string(xml_input: str) -> str: return core_ops.to_string(xml_input)
@mcp.tool()
def to_pretty_string(xml_input: str) -> str: return core_ops.to_pretty_string(xml_input)
@mcp.tool()
def strip_tags(xml_input: str, tags: List[str]) -> str: return core_ops.strip_tags(xml_input, tags)
@mcp.tool()
def strip_elements(xml_input: str, tags: List[str]) -> str: return core_ops.strip_elements(xml_input, tags)
@mcp.tool()
def get_element_text(xml_input: str, xpath: str = ".") -> str: return core_ops.get_element_text(xml_input, xpath)
@mcp.tool()
def get_element_attrs(xml_input: str, xpath: str = ".") -> Dict[str, str]: return core_ops.get_element_attrs(xml_input, xpath)

# ==========================================
# 2. XPath & Select
# ==========================================
@mcp.tool()
def xpath_query(xml_input: str, query: str) -> List[str]: return xpath_ops.xpath_query(xml_input, query)
@mcp.tool()
def xpath_query_text(xml_input: str, query: str) -> List[str]: return xpath_ops.xpath_query_text(xml_input, query)
@mcp.tool()
def xpath_query_attr(xml_input: str, query: str) -> List[str]: return xpath_ops.xpath_query_attr(xml_input, query)
@mcp.tool()
def css_select(xml_input: str, selector: str) -> List[str]: return xpath_ops.css_select(xml_input, selector)
@mcp.tool()
def get_parent(xml_input: str, xpath: str) -> str: return xpath_ops.get_parent(xml_input, xpath)
@mcp.tool()
def get_children(xml_input: str, xpath: str) -> List[str]: return xpath_ops.get_children(xml_input, xpath)
@mcp.tool()
def get_siblings(xml_input: str, xpath: str) -> Dict[str, str]: return xpath_ops.get_siblings(xml_input, xpath)

# ==========================================
# 3. Transform & Clean
# ==========================================
@mcp.tool()
def xslt_transform(xml_input: str, xslt_input: str) -> str: return transform_ops.xslt_transform(xml_input, xslt_input)
@mcp.tool()
def clean_html(html_input: str) -> str: return transform_ops.clean_html(html_input)
@mcp.tool()
def make_links_absolute(html_input: str, base_url: str) -> str: return transform_ops.make_links_absolute(html_input, base_url)
@mcp.tool()
def remove_javascript(html_input: str) -> str: return transform_ops.remove_javascript(html_input)
@mcp.tool()
def builder_create(tag: str, text: str, **attrs) -> str: return transform_ops.builder_create(tag, text, **attrs)
@mcp.tool()
def add_child(xml_input: str, parent_xpath: str, child_tag: str, child_text: str) -> str: return transform_ops.add_child(xml_input, parent_xpath, child_tag, child_text)
@mcp.tool()
def set_attribute(xml_input: str, xpath: str, key: str, value: str) -> str: return transform_ops.set_attribute(xml_input, xpath, key, value)
@mcp.tool()
def remove_attribute(xml_input: str, xpath: str, key: str) -> str: return transform_ops.remove_attribute(xml_input, xpath, key)
@mcp.tool()
def replace_element(xml_input: str, xpath: str, new_tag: str) -> str: return transform_ops.replace_element(xml_input, xpath, new_tag)

# ==========================================
# 4. Validate
# ==========================================
@mcp.tool()
def validate_dtd(xml_input: str, dtd_input: str) -> str: return validate_ops.validate_dtd(xml_input, dtd_input)
@mcp.tool()
def validate_xsd(xml_input: str, xsd_input: str) -> str: return validate_ops.validate_xsd(xml_input, xsd_input)
@mcp.tool()
def validate_relaxng(xml_input: str, rng_input: str) -> str: return validate_ops.validate_relaxng(xml_input, rng_input)
@mcp.tool()
def validate_schematron(xml_input: str, schema_input: str) -> str: return validate_ops.validate_schematron(xml_input, schema_input)
@mcp.tool()
def check_well_formed(xml_input: str) -> bool: return validate_ops.check_well_formed(xml_input)

# ==========================================
# 5. Objectify
# ==========================================
@mcp.tool()
def objectify_parse(xml_input: str) -> str: return objectify_ops.objectify_parse(xml_input)
@mcp.tool()
def objectify_dump(xml_input: str) -> str: return objectify_ops.objectify_dump(xml_input)
@mcp.tool()
def data_element_create(value: Any, type_annotation: str = None) -> str: return objectify_ops.data_element_create(value, type_annotation)

# ==========================================
# 6. Bulk
# ==========================================
@mcp.tool()
def iterparse_counts(file_path: str, tag: str) -> int: return bulk_ops.iterparse_counts(file_path, tag)
@mcp.tool()
def iterparse_extract(file_path: str, tag: str, limit: int = 100000) -> List[str]: return bulk_ops.iterparse_extract(file_path, tag, limit)
@mcp.tool()
def bulk_xpath_files(directory: str, xpath: str, extension: str = "*.xml") -> Dict[str, List[str]]: return bulk_ops.bulk_xpath_files(directory, xpath, extension)
@mcp.tool()
def bulk_validate_xsd(directory: str, xsd_path: str) -> Dict[str, str]: return bulk_ops.bulk_validate_xsd(directory, xsd_path)
@mcp.tool()
def bulk_transform_xslt(directory: str, xslt_path: str, output_dir: str) -> str: return bulk_ops.bulk_transform_xslt(directory, xslt_path, output_dir)
@mcp.tool()
def grep_elements_dir(directory: str, search_text: str) -> Dict[str, List[str]]: return bulk_ops.grep_elements_dir(directory, search_text)
@mcp.tool()
def map_xml_structure(directory: str) -> Dict[str, str]: return bulk_ops.map_xml_structure(directory)

# ==========================================
# 7. Super
# ==========================================
@mcp.tool()
def html_table_to_json(html_input: str) -> str: return super_ops.html_table_to_json(html_input)
@mcp.tool()
def web_scraper_simple(url: str, xpath: str) -> List[str]: return super_ops.web_scraper_simple(url, xpath)
@mcp.tool()
def diff_xml_trees(xml_a: str, xml_b: str) -> str: return super_ops.diff_xml_trees(xml_a, xml_b)
@mcp.tool()
def merge_xml_trees(xml_strings: List[str], root_tag: str = "merged") -> str: return super_ops.merge_xml_trees(xml_strings, root_tag)
@mcp.tool()
def xml_to_dict_lxml(xml_input: str) -> str: return super_ops.xml_to_dict_lxml(xml_input)
@mcp.tool()
def dict_to_xml_lxml(json_input: str) -> str: return super_ops.dict_to_xml_lxml(json_input)
@mcp.tool()
def extract_links_bulk(directory: str) -> Dict[str, List[str]]: return super_ops.extract_links_bulk(directory)
@mcp.tool()
def auto_fix_html(html_input: str) -> str: return super_ops.auto_fix_html(html_input)
@mcp.tool()
def generate_rss_item(title: str, link: str, desc: str) -> str: return super_ops.generate_rss_item(title, link, desc)
@mcp.tool()
def xinclude_process(xml_input: str) -> str: return super_ops.xinclude_process(xml_input)
@mcp.tool()
def visualize_tree_structure(xml_input: str) -> str: return super_ops.visualize_tree_structure(xml_input)
@mcp.tool()
def minify_xml(xml_input: str) -> str: return super_ops.minify_xml(xml_input)
@mcp.tool()
def benchmark_parsing(file_size_mb: int = 10) -> str: return super_ops.benchmark_parsing(file_size_mb)
@mcp.tool()
def anonymize_xml_content(xml_input: str) -> str: return super_ops.anonymize_xml_content(xml_input)

if __name__ == "__main__":
    mcp.run()
