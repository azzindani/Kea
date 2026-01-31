# /// script
# dependencies = [
#   "mcp",
#   "beautifulsoup4",
#   "lxml",
#   "html5lib",
#   "structlog"
# ]
# ///

from mcp.server.fastmcp import FastMCP
from mcp_servers.bs4_server.soup_manager import SoupManager
from mcp_servers.bs4_server.tools import (
    core_ops, nav_ops, search_ops, extract_ops, mod_ops, super_ops,
    convert_ops, sanitize_ops, analyze_ops, fix_ops, logic_ops,
    semantic_ops, feed_ops, diff_ops, visual_ops, export_ops
)
import structlog
from typing import List, Dict, Any, Optional, Union

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("bs4_server", dependencies=["beautifulsoup4", "lxml", "html5lib"])

# ==========================================
# 0. Core
# ==========================================
@mcp.tool()
async def parse_html(html: str) -> str: return await core_ops.parse_html(html)
@mcp.tool()
async def load_file(path: str) -> str: return await core_ops.load_file(path)
@mcp.tool()
async def save_file(soup_id: str, path: str) -> str: return await core_ops.save_file(soup_id, path)
@mcp.tool()
async def prettify(soup_id: Optional[str] = None) -> str: return await core_ops.prettify_soup(soup_id)
@mcp.tool()
async def close_soup(soup_id: str) -> str: return await core_ops.close_soup(soup_id)
@mcp.tool()
async def get_stats(soup_id: Optional[str] = None) -> Dict[str, Any]: return await core_ops.get_soup_stats(soup_id)

# ==========================================
# 1. Navigation
# ==========================================
@mcp.tool()
async def get_parent(selector: str, soup_id: Optional[str] = None) -> Dict[str, Any]: return await nav_ops.get_parent(selector, soup_id)
@mcp.tool()
async def get_children(selector: str, soup_id: Optional[str] = None) -> List[Dict[str, Any]]: return await nav_ops.get_children(selector, soup_id)
@mcp.tool()
async def get_siblings(selector: str, soup_id: Optional[str] = None) -> Dict[str, Any]: return await nav_ops.get_siblings(selector, soup_id)
@mcp.tool()
async def get_path(selector: str, soup_id: Optional[str] = None) -> str: return await nav_ops.get_path(selector, soup_id)

# ==========================================
# 2. Search
# ==========================================
@mcp.tool()
async def select_one(selector: str, soup_id: Optional[str] = None) -> str: return await search_ops.select_one(selector, soup_id)
@mcp.tool()
async def select_all(selector: str, limit: int = 0, soup_id: Optional[str] = None) -> List[str]: return await search_ops.select_all(selector, limit, soup_id)
@mcp.tool()
async def find_tag(name: str, attrs: Dict[str, Any] = {}, soup_id: Optional[str] = None) -> str: return await search_ops.find_tag(name, attrs, soup_id)
@mcp.tool()
async def find_all_tags(name: str, attrs: Dict[str, Any] = {}, limit: int = 0, soup_id: Optional[str] = None) -> List[str]: return await search_ops.find_all_tags(name, attrs, limit, soup_id)
@mcp.tool()
async def find_by_text(text_regex: str, soup_id: Optional[str] = None) -> List[str]: return await search_ops.find_by_text(text_regex, soup_id)
@mcp.tool()
async def find_by_id(element_id: str, soup_id: Optional[str] = None) -> str: return await search_ops.find_by_id(element_id, soup_id)
@mcp.tool()
async def find_by_class(class_name: str, soup_id: Optional[str] = None) -> List[str]: return await search_ops.find_by_class(class_name, soup_id)

# ==========================================
# 3. Extraction
# ==========================================
@mcp.tool()
async def get_text(selector: str, strip: bool = True, soup_id: Optional[str] = None) -> str: return await extract_ops.get_text(selector, strip, soup_id)
@mcp.tool()
async def get_all_text(selector: str, strip: bool = True, separator: str = "\\n", soup_id: Optional[str] = None) -> List[str]: return await extract_ops.get_all_text(selector, strip, separator, soup_id)
@mcp.tool()
async def get_attr(selector: str, attr: str, soup_id: Optional[str] = None) -> str: return await extract_ops.get_attr(selector, attr, soup_id)
@mcp.tool()
async def get_attrs(selector: str, soup_id: Optional[str] = None) -> Dict[str, Any]: return await extract_ops.get_attrs(selector, soup_id)
@mcp.tool()
async def get_all_attrs(selector: str, attr: str, soup_id: Optional[str] = None) -> List[str]: return await extract_ops.get_all_attrs(selector, attr, soup_id)
@mcp.tool()
async def get_classes(selector: str, soup_id: Optional[str] = None) -> List[str]: return await extract_ops.get_classes(selector, soup_id)
@mcp.tool()
async def get_data_attrs(selector: str, soup_id: Optional[str] = None) -> Dict[str, str]: return await extract_ops.get_data_attrs(selector, soup_id)

# ==========================================
# 4. Modification
# ==========================================
@mcp.tool()
async def decompose(selector: str, soup_id: Optional[str] = None) -> str: return await mod_ops.decompose_tag(selector, soup_id)
@mcp.tool()
async def extract(selector: str, soup_id: Optional[str] = None) -> str: return await mod_ops.extract_tag(selector, soup_id)
@mcp.tool()
async def replace_with(selector: str, new_html: str, soup_id: Optional[str] = None) -> str: return await mod_ops.replace_with(selector, new_html, soup_id)
@mcp.tool()
async def insert_after(selector: str, html: str, soup_id: Optional[str] = None) -> str: return await mod_ops.insert_after(selector, html, soup_id)
@mcp.tool()
async def insert_before(selector: str, html: str, soup_id: Optional[str] = None) -> str: return await mod_ops.insert_before(selector, html, soup_id)
@mcp.tool()
async def wrap(selector: str, wrapper_tag: str, soup_id: Optional[str] = None) -> str: return await mod_ops.wrap_tag(selector, wrapper_tag, soup_id)
@mcp.tool()
async def unwrap(selector: str, soup_id: Optional[str] = None) -> str: return await mod_ops.unwrap_tag(selector, soup_id)
@mcp.tool()
async def add_class(selector: str, class_name: str, soup_id: Optional[str] = None) -> str: return await mod_ops.add_class(selector, class_name, soup_id)
@mcp.tool()
async def remove_class(selector: str, class_name: str, soup_id: Optional[str] = None) -> str: return await mod_ops.remove_class(selector, class_name, soup_id)
@mcp.tool()
async def set_attr(selector: str, attr: str, value: str, soup_id: Optional[str] = None) -> str: return await mod_ops.set_attr(selector, attr, value, soup_id)

# ==========================================
# 5. Super Tools
# ==========================================
@mcp.tool()
async def bulk_extract(selector_map: Dict[str, str], scope: Optional[str] = None, soup_id: Optional[str] = None) -> Any: return await super_ops.bulk_extract_css(selector_map, scope, soup_id)
@mcp.tool()
async def clean_structure(remove_tags: List[str] = ["script", "style", "iframe"], soup_id: Optional[str] = None) -> str: return await super_ops.clean_html_structure(remove_tags, soup_id)
@mcp.tool()
async def extract_table(selector: str = "table", soup_id: Optional[str] = None) -> List[List[str]]: return await super_ops.extract_table_static(selector, soup_id)
@mcp.tool()
async def get_structure(max_depth: int = 3, soup_id: Optional[str] = None) -> Dict[str, Any]: return await super_ops.html_to_structure(max_depth, soup_id)

# ==========================================
# 6. Hyper Tools
# ==========================================
# Conversion
@mcp.tool()
async def to_markdown(selector: str = "body", soup_id: Optional[str] = None) -> str: return await convert_ops.html_to_markdown(selector, soup_id)
@mcp.tool()
async def minify(selector: str = "body", soup_id: Optional[str] = None) -> str: return await convert_ops.minify_html(selector, soup_id)
# Sanitize
@mcp.tool()
async def strip_attrs(selector: str, attrs: List[str] = ["style", "onclick"], soup_id: Optional[str] = None) -> str: return await sanitize_ops.strip_attributes(selector, attrs, soup_id)
@mcp.tool()
async def allowlist(keep_tags: List[str], selector: str = "body", soup_id: Optional[str] = None) -> str: return await sanitize_ops.allowlist_tags(keep_tags, selector, soup_id)
# Analysis
@mcp.tool()
async def analyze_links(soup_id: Optional[str] = None, base_url: Optional[str] = None) -> Dict[str, Any]: return await analyze_ops.analyze_links(soup_id, base_url)
@mcp.tool()
async def tag_frequency(soup_id: Optional[str] = None) -> Dict[str, int]: return await analyze_ops.tag_frequency(soup_id)
@mcp.tool()
async def text_density(selector: str = "body", soup_id: Optional[str] = None) -> float: return await analyze_ops.get_text_density(selector, soup_id)
# Fixes
@mcp.tool()
async def make_absolute(base_url: str, soup_id: Optional[str] = None) -> str: return await fix_ops.make_links_absolute(base_url, soup_id)
@mcp.tool()
async def normalize(selector: str = "div", soup_id: Optional[str] = None) -> str: return await fix_ops.normalize_structure(selector, soup_id)
# Logic
@mcp.tool()
async def remove_if_contains(text_regex: str, selector: str = "div", soup_id: Optional[str] = None) -> str: return await logic_ops.remove_if_contains(text_regex, selector, soup_id)
@mcp.tool()
async def isolate(selector: str, soup_id: Optional[str] = None) -> str: return await logic_ops.isolate_element(selector, soup_id)

# ==========================================
# 7. Ultimate Tools (New)
# ==========================================
# Semantic
@mcp.tool()
async def get_jsonld(soup_id: Optional[str] = None) -> List[Dict[str, Any]]: return await semantic_ops.extract_jsonld(soup_id)
@mcp.tool()
async def get_opengraph(soup_id: Optional[str] = None) -> Dict[str, str]: return await semantic_ops.extract_opengraph(soup_id)
@mcp.tool()
async def get_meta_tags(soup_id: Optional[str] = None) -> Dict[str, str]: return await semantic_ops.extract_meta_tags(soup_id)
@mcp.tool()
async def get_microdata(soup_id: Optional[str] = None) -> List[Dict[str, Any]]: return await semantic_ops.extract_microdata(soup_id)
# Feed
@mcp.tool()
async def find_feeds(soup_id: Optional[str] = None) -> List[Dict[str, str]]: return await feed_ops.find_feed_links(soup_id)
@mcp.tool()
async def read_rss(soup_id: Optional[str] = None) -> List[Dict[str, str]]: return await feed_ops.extract_rss_items(soup_id)
# Diff
@mcp.tool()
async def diff_text(selector: str, other_html: str, soup_id: Optional[str] = None) -> str: return await diff_ops.diff_text(selector, other_html, soup_id)
@mcp.tool()
async def diff_attrs(selector: str, other_html: str, soup_id: Optional[str] = None) -> Dict[str, Any]: return await diff_ops.diff_attributes(selector, other_html, soup_id)
# Visual
@mcp.tool()
async def view_tree(selector: str = "body", depth: int = 3, soup_id: Optional[str] = None) -> str: return await visual_ops.render_tree(selector, depth, soup_id)
@mcp.tool()
async def view_layout(selector: str = "body", soup_id: Optional[str] = None) -> str: return await visual_ops.render_layout(selector, soup_id=soup_id)
# Export
@mcp.tool()
async def to_csv(selector: str, soup_id: Optional[str] = None) -> str: 
    # Auto-detect table or list? Or separate tools?
    # Let's map strict tools for better control
    return "Use table_to_csv or list_to_csv"
@mcp.tool()
async def table_to_csv(selector: str = "table", soup_id: Optional[str] = None) -> str: return await export_ops.table_to_csv(selector, soup_id)
@mcp.tool()
async def list_to_csv(selector: str = "ul", soup_id: Optional[str] = None) -> str: return await export_ops.list_to_csv(selector, soup_id)
@mcp.tool()
async def to_jsonl(selector: str, mode: str = "text", soup_id: Optional[str] = None) -> str: return await export_ops.to_jsonl(selector, mode, soup_id)


if __name__ == "__main__":
    mcp.run()
