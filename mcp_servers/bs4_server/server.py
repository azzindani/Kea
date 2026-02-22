
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)


from shared.mcp.fastmcp import FastMCP
from soup_manager import SoupManager
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.bs4_server.tools import (
    core_ops, nav_ops, search_ops, extract_ops, mod_ops, super_ops,
    convert_ops, sanitize_ops, analyze_ops, fix_ops, logic_ops,
    semantic_ops, feed_ops, diff_ops, visual_ops, export_ops
)
import structlog
from typing import List, Dict, Any, Optional, Union

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging(force_stderr=True)

mcp = FastMCP("bs4_server", dependencies=["beautifulsoup4", "lxml", "html5lib"])

# ==========================================
# 0. Core
# ==========================================
# ==========================================
# 0. Core
# ==========================================
@mcp.tool()
async def parse_html(html: str) -> str: 
    """PARSES HTML string. [ACTION]
    
    [RAG Context]
    Returns soup_id.
    """
    return await core_ops.parse_html(html)

@mcp.tool()
async def load_file(path: str) -> str: 
    """LOADS HTML file. [DATA]
    
    [RAG Context]
    Returns soup_id.
    """
    return await core_ops.load_file(path)

@mcp.tool()
async def save_file(soup_id: str, path: str) -> str: 
    """SAVES HTML to file. [ACTION]
    
    [RAG Context]
    """
    return await core_ops.save_file(soup_id, path)

@mcp.tool()
async def prettify(soup_id: Optional[str] = None) -> str: 
    """FORMATS HTML code. [ACTION]
    
    [RAG Context]
    """
    return await core_ops.prettify_soup(soup_id)

@mcp.tool()
async def close_soup(soup_id: str) -> str: 
    """FREES memory. [ACTION]
    
    [RAG Context]
    """
    return await core_ops.close_soup(soup_id)

@mcp.tool()
async def get_stats(soup_id: Optional[str] = None) -> Dict[str, Any]: 
    """GETS soup stats. [DATA]
    
    [RAG Context]
    Node count, depth.
    """
    return await core_ops.get_soup_stats(soup_id)

# ==========================================
# 1. Navigation
# ==========================================
@mcp.tool()
async def get_parent(selector: str, soup_id: Optional[str] = None) -> Dict[str, Any]: 
    """GETS parent element. [DATA]
    
    [RAG Context]
    """
    return await nav_ops.get_parent(selector, soup_id)

@mcp.tool()
async def get_children(selector: str, soup_id: Optional[str] = None) -> List[Dict[str, Any]]: 
    """GETS child elements. [DATA]
    
    [RAG Context]
    """
    return await nav_ops.get_children(selector, soup_id)

@mcp.tool()
async def get_siblings(selector: str, soup_id: Optional[str] = None) -> Dict[str, Any]: 
    """GETS sibling elements. [DATA]
    
    [RAG Context]
    """
    return await nav_ops.get_siblings(selector, soup_id)

@mcp.tool()
async def get_path(selector: str, soup_id: Optional[str] = None) -> str: 
    """GETS CSS path. [DATA]
    
    [RAG Context]
    """
    return await nav_ops.get_path(selector, soup_id)

# ==========================================
# 2. Search
# ==========================================
@mcp.tool()
async def select_one(selector: str, soup_id: Optional[str] = None) -> str: 
    """FINDS first match (CSS). [DATA]
    
    [RAG Context]
    """
    return await search_ops.select_one(selector, soup_id)

@mcp.tool()
async def select_all(selector: str, limit: int = 0, soup_id: Optional[str] = None) -> List[str]: 
    """FINDS all matches (CSS). [DATA]
    
    [RAG Context]
    """
    return await search_ops.select_all(selector, limit, soup_id)

@mcp.tool()
async def find_tag(name: str, attrs: Dict[str, Any] = {}, soup_id: Optional[str] = None) -> str: 
    """FINDS first tag. [DATA]
    
    [RAG Context]
    """
    return await search_ops.find_tag(name, attrs, soup_id)

@mcp.tool()
async def find_all_tags(name: str, attrs: Dict[str, Any] = {}, limit: int = 0, soup_id: Optional[str] = None) -> List[str]: 
    """FINDS all tags. [DATA]
    
    [RAG Context]
    """
    return await search_ops.find_all_tags(name, attrs, limit, soup_id)

@mcp.tool()
async def find_by_text(text_regex: str, soup_id: Optional[str] = None) -> List[str]: 
    """FINDS elements by text. [DATA]
    
    [RAG Context]
    """
    return await search_ops.find_by_text(text_regex, soup_id)

@mcp.tool()
async def find_by_id(element_id: str, soup_id: Optional[str] = None) -> str: 
    """FINDS element by ID. [DATA]
    
    [RAG Context]
    """
    return await search_ops.find_by_id(element_id, soup_id)

@mcp.tool()
async def find_by_class(class_name: str, soup_id: Optional[str] = None) -> List[str]: 
    """FINDS elements by class. [DATA]
    
    [RAG Context]
    """
    return await search_ops.find_by_class(class_name, soup_id)

# ==========================================
# 3. Extraction
# ==========================================
# ==========================================
# 3. Extraction
# ==========================================
@mcp.tool()
async def get_text(selector: str, strip: bool = True, soup_id: Optional[str] = None) -> str: 
    """EXTRACTS text from element. [DATA]
    
    [RAG Context]
    """
    return await extract_ops.get_text(selector, strip, soup_id)

@mcp.tool()
async def get_all_text(selector: str, strip: bool = True, separator: str = "\\n", soup_id: Optional[str] = None) -> List[str]: 
    """EXTRACTS text list. [DATA]
    
    [RAG Context]
    """
    return await extract_ops.get_all_text(selector, strip, separator, soup_id)

@mcp.tool()
async def get_attr(selector: str, attr: str, soup_id: Optional[str] = None) -> str: 
    """GETS attribute value. [DATA]
    
    [RAG Context]
    """
    return await extract_ops.get_attr(selector, attr, soup_id)

@mcp.tool()
async def get_attrs(selector: str, soup_id: Optional[str] = None) -> Dict[str, Any]: 
    """GETS all attributes. [DATA]
    
    [RAG Context]
    """
    return await extract_ops.get_attrs(selector, soup_id)

@mcp.tool()
async def get_all_attrs(selector: str, attr: str, soup_id: Optional[str] = None) -> List[str]: 
    """GETS attribute list. [DATA]
    
    [RAG Context]
    From all matching elements.
    """
    return await extract_ops.get_all_attrs(selector, attr, soup_id)

@mcp.tool()
async def get_classes(selector: str, soup_id: Optional[str] = None) -> List[str]: 
    """GETS classes. [DATA]
    
    [RAG Context]
    """
    return await extract_ops.get_classes(selector, soup_id)

@mcp.tool()
async def get_data_attrs(selector: str, soup_id: Optional[str] = None) -> Dict[str, str]: 
    """GETS data-* attributes. [DATA]
    
    [RAG Context]
    """
    return await extract_ops.get_data_attrs(selector, soup_id)

# ==========================================
# 4. Modification
# ==========================================
@mcp.tool()
async def decompose(selector: str, soup_id: Optional[str] = None) -> str: 
    """REMOVES element permanently. [ACTION]
    
    [RAG Context]
    Destructive.
    """
    return await mod_ops.decompose_tag(selector, soup_id)

@mcp.tool()
async def extract(selector: str, soup_id: Optional[str] = None) -> str: 
    """REMOVES and returns element. [ACTION]
    
    [RAG Context]
    """
    return await mod_ops.extract_tag(selector, soup_id)

@mcp.tool()
async def replace_with(selector: str, new_html: str, soup_id: Optional[str] = None) -> str: 
    """REPLACES element. [ACTION]
    
    [RAG Context]
    """
    return await mod_ops.replace_with(selector, new_html, soup_id)

@mcp.tool()
async def insert_after(selector: str, html: str, soup_id: Optional[str] = None) -> str: 
    """INSERTS HTML after. [ACTION]
    
    [RAG Context]
    """
    return await mod_ops.insert_after(selector, html, soup_id)

@mcp.tool()
async def insert_before(selector: str, html: str, soup_id: Optional[str] = None) -> str: 
    """INSERTS HTML before. [ACTION]
    
    [RAG Context]
    """
    return await mod_ops.insert_before(selector, html, soup_id)

@mcp.tool()
async def wrap(selector: str, wrapper_tag: str, soup_id: Optional[str] = None) -> str: 
    """WRAPS element in tag. [ACTION]
    
    [RAG Context]
    """
    return await mod_ops.wrap_tag(selector, wrapper_tag, soup_id)

@mcp.tool()
async def unwrap(selector: str, soup_id: Optional[str] = None) -> str: 
    """REMOVES parent tag. [ACTION]
    
    [RAG Context]
    """
    return await mod_ops.unwrap_tag(selector, soup_id)

@mcp.tool()
async def add_class(selector: str, class_name: str, soup_id: Optional[str] = None) -> str: 
    """ADDS CSS class. [ACTION]
    
    [RAG Context]
    """
    return await mod_ops.add_class(selector, class_name, soup_id)

@mcp.tool()
async def remove_class(selector: str, class_name: str, soup_id: Optional[str] = None) -> str: 
    """REMOVES CSS class. [ACTION]
    
    [RAG Context]
    """
    return await mod_ops.remove_class(selector, class_name, soup_id)

@mcp.tool()
async def set_attr(selector: str, attr: str, value: str, soup_id: Optional[str] = None) -> str: 
    """SETS attribute. [ACTION]
    
    [RAG Context]
    """
    return await mod_ops.set_attr(selector, attr, value, soup_id)

# ==========================================
# 5. Super Tools
# ==========================================
# ==========================================
# 5. Super Tools
# ==========================================
@mcp.tool()
async def bulk_extract(selector_map: Dict[str, str], scope: Optional[str] = None, soup_id: Optional[str] = None) -> Any: 
    """EXTRACTS multiple fields (CSS). [DATA]
    
    [RAG Context]
    """
    return await super_ops.bulk_extract_css(selector_map, scope, soup_id)

@mcp.tool()
async def clean_structure(remove_tags: List[str] = ["script", "style", "iframe"], soup_id: Optional[str] = None) -> str: 
    """REMOVES dangerous/unwanted tags. [ACTION]
    
    [RAG Context]
    """
    return await super_ops.clean_html_structure(remove_tags, soup_id)

@mcp.tool()
async def extract_table(selector: str = "table", soup_id: Optional[str] = None) -> List[List[str]]: 
    """EXTRACTS table as list. [DATA]
    
    [RAG Context]
    """
    return await super_ops.extract_table_static(selector, soup_id)

@mcp.tool()
async def get_structure(max_depth: int = 3, soup_id: Optional[str] = None) -> Dict[str, Any]: 
    """GETS DOM tree structure. [DATA]
    
    [RAG Context]
    """
    return await super_ops.html_to_structure(max_depth, soup_id)

# ==========================================
# 6. Hyper Tools
# ==========================================
# Conversion
@mcp.tool()
async def to_markdown(selector: str = "body", soup_id: Optional[str] = None) -> str: 
    """CONVERTS to Markdown. [DATA]
    
    [RAG Context]
    """
    return await convert_ops.html_to_markdown(selector, soup_id)

@mcp.tool()
async def minify(selector: str = "body", soup_id: Optional[str] = None) -> str: 
    """MINIFIES HTML. [ACTION]
    
    [RAG Context]
    """
    return await convert_ops.minify_html(selector, soup_id)

# Sanitize
@mcp.tool()
async def strip_attrs(selector: str, attrs: List[str] = ["style", "onclick"], soup_id: Optional[str] = None) -> str: 
    """REMOVES attributes. [ACTION]
    
    [RAG Context]
    """
    return await sanitize_ops.strip_attributes(selector, attrs, soup_id)

@mcp.tool()
async def allowlist(keep_tags: List[str], selector: str = "body", soup_id: Optional[str] = None) -> str: 
    """KEEPS only allowed tags. [ACTION]
    
    [RAG Context]
    """
    return await sanitize_ops.allowlist_tags(keep_tags, selector, soup_id)

# Analysis
@mcp.tool()
async def analyze_links(soup_id: Optional[str] = None, base_url: Optional[str] = None) -> Dict[str, Any]: 
    """ANALYZES all links. [DATA]
    
    [RAG Context]
    """
    return await analyze_ops.analyze_links(soup_id, base_url)

@mcp.tool()
async def tag_frequency(soup_id: Optional[str] = None) -> Dict[str, int]: 
    """COUNTS tag usage. [DATA]
    
    [RAG Context]
    """
    return await analyze_ops.tag_frequency(soup_id)

@mcp.tool()
async def text_density(selector: str = "body", soup_id: Optional[str] = None) -> float: 
    """CALCULATES text ratio. [DATA]
    
    [RAG Context]
    """
    return await analyze_ops.get_text_density(selector, soup_id)

# Fixes
@mcp.tool()
async def make_absolute(base_url: str, soup_id: Optional[str] = None) -> str: 
    """CONVERTS links to absolute. [ACTION]
    
    [RAG Context]
    """
    return await fix_ops.make_links_absolute(base_url, soup_id)

@mcp.tool()
async def normalize(selector: str = "div", soup_id: Optional[str] = None) -> str: 
    """NORMALIZES spacing/structure. [ACTION]
    
    [RAG Context]
    """
    return await fix_ops.normalize_structure(selector, soup_id)

# Logic
@mcp.tool()
async def remove_if_contains(text_regex: str, selector: str = "div", soup_id: Optional[str] = None) -> str: 
    """REMOVES element if text match. [ACTION]
    
    [RAG Context]
    """
    return await logic_ops.remove_if_contains(text_regex, selector, soup_id)

@mcp.tool()
async def isolate(selector: str, soup_id: Optional[str] = None) -> str: 
    """REMOVES everything else. [ACTION]
    
    [RAG Context]
    """
    return await logic_ops.isolate_element(selector, soup_id)

# ==========================================
# 7. Ultimate Tools (New)
# ==========================================
# Semantic
@mcp.tool()
async def get_jsonld(soup_id: Optional[str] = None) -> List[Dict[str, Any]]: 
    """EXTRACTS structured data (JSON-LD). [DATA]
    
    [RAG Context]
    """
    return await semantic_ops.extract_jsonld(soup_id)

@mcp.tool()
async def get_opengraph(soup_id: Optional[str] = None) -> Dict[str, str]: 
    """EXTRACTS OpenGraph metadata. [DATA]
    
    [RAG Context]
    """
    return await semantic_ops.extract_opengraph(soup_id)

@mcp.tool()
async def get_meta_tags(soup_id: Optional[str] = None) -> Dict[str, str]: 
    """EXTRACTS meta tags. [DATA]
    
    [RAG Context]
    """
    return await semantic_ops.extract_meta_tags(soup_id)

@mcp.tool()
async def get_microdata(soup_id: Optional[str] = None) -> List[Dict[str, Any]]: 
    """EXTRACTS Microdata. [DATA]
    
    [RAG Context]
    """
    return await semantic_ops.extract_microdata(soup_id)

# Feed
@mcp.tool()
async def find_feeds(soup_id: Optional[str] = None) -> List[Dict[str, str]]: 
    """FINDS RSS/Atom feeds. [DATA]
    
    [RAG Context]
    """
    return await feed_ops.find_feed_links(soup_id)

@mcp.tool()
async def read_rss(soup_id: Optional[str] = None) -> List[Dict[str, str]]: 
    """PARSES RSS feed. [DATA]
    
    [RAG Context]
    """
    return await feed_ops.extract_rss_items(soup_id)

# Diff
@mcp.tool()
async def diff_text(selector: str, other_html: str, soup_id: Optional[str] = None) -> str: 
    """DIFFS text content. [DATA]
    
    [RAG Context]
    """
    return await diff_ops.diff_text(selector, other_html, soup_id)

@mcp.tool()
async def diff_attrs(selector: str, other_html: str, soup_id: Optional[str] = None) -> Dict[str, Any]: 
    """DIFFS attributes. [DATA]
    
    [RAG Context]
    """
    return await diff_ops.diff_attributes(selector, other_html, soup_id)

# Visual
@mcp.tool()
async def view_tree(selector: str = "body", depth: int = 3, soup_id: Optional[str] = None) -> str: 
    """RENDERS DOM tree text. [DATA]
    
    [RAG Context]
    """
    return await visual_ops.render_tree(selector, depth, soup_id)

@mcp.tool()
async def view_layout(selector: str = "body", soup_id: Optional[str] = None) -> str: 
    """RENDERS approximate layout. [DATA]
    
    [RAG Context]
    """
    return await visual_ops.render_layout(selector, soup_id=soup_id)

# Export
@mcp.tool()
async def to_csv(selector: str, soup_id: Optional[str] = None) -> str: 
    # Auto-detect table or list? Or separate tools?
    # Let's map strict tools for better control
    return "Use table_to_csv or list_to_csv"

@mcp.tool()
async def table_to_csv(selector: str = "table", soup_id: Optional[str] = None) -> str: 
    """CONVERTS table to CSV. [DATA]
    
    [RAG Context]
    """
    return await export_ops.table_to_csv(selector, soup_id)

@mcp.tool()
async def list_to_csv(selector: str = "ul", soup_id: Optional[str] = None) -> str: 
    """CONVERTS list to CSV. [DATA]
    
    [RAG Context]
    """
    return await export_ops.list_to_csv(selector, soup_id)

@mcp.tool()
async def to_jsonl(selector: str, mode: str = "text", soup_id: Optional[str] = None) -> str: 
    """CONVERTS content to JSONL. [DATA]
    
    [RAG Context]
    """
    return await export_ops.to_jsonl(selector, mode, soup_id)

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class Bs4Server:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []

