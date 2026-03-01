# 🔌 Bs4 Server

The `bs4_server` is an MCP server providing tools for **Bs4 Server** functionality.
It is designed to be used within the Project ecosystem.

## 🧰 Tools

| Tool | Description | Arguments |
|:-----|:------------|:----------|
| `parse_html` | Execute parse html operation | `html: str` |
| `load_file` | Execute load file operation | `path: str` |
| `save_file` | Execute save file operation | `soup_id: str, path: str` |
| `prettify` | Execute prettify operation | `soup_id: Optional[str] = None` |
| `close_soup` | Execute close soup operation | `soup_id: str` |
| `get_stats` | Execute get stats operation | `soup_id: Optional[str] = None` |
| `get_parent` | Execute get parent operation | `selector: str, soup_id: Optional[str] = None` |
| `get_children` | Execute get children operation | `selector: str, soup_id: Optional[str] = None` |
| `get_siblings` | Execute get siblings operation | `selector: str, soup_id: Optional[str] = None` |
| `get_path` | Execute get path operation | `selector: str, soup_id: Optional[str] = None` |
| `select_one` | Execute select one operation | `selector: str, soup_id: Optional[str] = None` |
| `select_all` | Execute select all operation | `selector: str, limit: int = 0, soup_id: Optional[str] = None` |
| `find_tag` | Execute find tag operation | `name: str, attrs: Dict[str, Any] = {}, soup_id: Optional[str] = None` |
| `find_all_tags` | Execute find all tags operation | `name: str, attrs: Dict[str, Any] = {}, limit: int = 0, soup_id: Optional[str] = None` |
| `find_by_text` | Execute find by text operation | `text_regex: str, soup_id: Optional[str] = None` |
| `find_by_id` | Execute find by id operation | `element_id: str, soup_id: Optional[str] = None` |
| `find_by_class` | Execute find by class operation | `class_name: str, soup_id: Optional[str] = None` |
| `get_text` | Execute get text operation | `selector: str, strip: bool = True, soup_id: Optional[str] = None` |
| `get_all_text` | Execute get all text operation | `selector: str, strip: bool = True, separator: str = "\\n", soup_id: Optional[str] = None` |
| `get_attr` | Execute get attr operation | `selector: str, attr: str, soup_id: Optional[str] = None` |
| `get_attrs` | Execute get attrs operation | `selector: str, soup_id: Optional[str] = None` |
| `get_all_attrs` | Execute get all attrs operation | `selector: str, attr: str, soup_id: Optional[str] = None` |
| `get_classes` | Execute get classes operation | `selector: str, soup_id: Optional[str] = None` |
| `get_data_attrs` | Execute get data attrs operation | `selector: str, soup_id: Optional[str] = None` |
| `decompose` | Execute decompose operation | `selector: str, soup_id: Optional[str] = None` |
| `extract` | Execute extract operation | `selector: str, soup_id: Optional[str] = None` |
| `replace_with` | Execute replace with operation | `selector: str, new_html: str, soup_id: Optional[str] = None` |
| `insert_after` | Execute insert after operation | `selector: str, html: str, soup_id: Optional[str] = None` |
| `insert_before` | Execute insert before operation | `selector: str, html: str, soup_id: Optional[str] = None` |
| `wrap` | Execute wrap operation | `selector: str, wrapper_tag: str, soup_id: Optional[str] = None` |
| `unwrap` | Execute unwrap operation | `selector: str, soup_id: Optional[str] = None` |
| `add_class` | Execute add class operation | `selector: str, class_name: str, soup_id: Optional[str] = None` |
| `remove_class` | Execute remove class operation | `selector: str, class_name: str, soup_id: Optional[str] = None` |
| `set_attr` | Execute set attr operation | `selector: str, attr: str, value: str, soup_id: Optional[str] = None` |
| `bulk_extract` | Execute bulk extract operation | `selector_map: Dict[str, str], scope: Optional[str] = None, soup_id: Optional[str] = None` |
| `clean_structure` | Execute clean structure operation | `remove_tags: List[str] = ["script", "style", "iframe"], soup_id: Optional[str] = None` |
| `extract_table` | Execute extract table operation | `selector: str = "table", soup_id: Optional[str] = None` |
| `get_structure` | Execute get structure operation | `max_depth: int = 3, soup_id: Optional[str] = None` |
| `to_markdown` | Execute to markdown operation | `selector: str = "body", soup_id: Optional[str] = None` |
| `minify` | Execute minify operation | `selector: str = "body", soup_id: Optional[str] = None` |
| `strip_attrs` | Execute strip attrs operation | `selector: str, attrs: List[str] = ["style", "onclick"], soup_id: Optional[str] = None` |
| `allowlist` | Execute allowlist operation | `keep_tags: List[str], selector: str = "body", soup_id: Optional[str] = None` |
| `analyze_links` | Execute analyze links operation | `soup_id: Optional[str] = None, base_url: Optional[str] = None` |
| `tag_frequency` | Execute tag frequency operation | `soup_id: Optional[str] = None` |
| `text_density` | Execute text density operation | `selector: str = "body", soup_id: Optional[str] = None` |
| `make_absolute` | Execute make absolute operation | `base_url: str, soup_id: Optional[str] = None` |
| `normalize` | Execute normalize operation | `selector: str = "div", soup_id: Optional[str] = None` |
| `remove_if_contains` | Execute remove if contains operation | `text_regex: str, selector: str = "div", soup_id: Optional[str] = None` |
| `isolate` | Execute isolate operation | `selector: str, soup_id: Optional[str] = None` |
| `get_jsonld` | Execute get jsonld operation | `soup_id: Optional[str] = None` |
| `get_opengraph` | Execute get opengraph operation | `soup_id: Optional[str] = None` |
| `get_meta_tags` | Execute get meta tags operation | `soup_id: Optional[str] = None` |
| `get_microdata` | Execute get microdata operation | `soup_id: Optional[str] = None` |
| `find_feeds` | Execute find feeds operation | `soup_id: Optional[str] = None` |
| `read_rss` | Execute read rss operation | `soup_id: Optional[str] = None` |
| `diff_text` | Execute diff text operation | `selector: str, other_html: str, soup_id: Optional[str] = None` |
| `diff_attrs` | Execute diff attrs operation | `selector: str, other_html: str, soup_id: Optional[str] = None` |
| `view_tree` | Execute view tree operation | `selector: str = "body", depth: int = 3, soup_id: Optional[str] = None` |
| `view_layout` | Execute view layout operation | `selector: str = "body", soup_id: Optional[str] = None` |
| `to_csv` | Execute to csv operation | `selector: str, soup_id: Optional[str] = None` |
| `table_to_csv` | Execute table to csv operation | `selector: str = "table", soup_id: Optional[str] = None` |
| `list_to_csv` | Execute list to csv operation | `selector: str = "ul", soup_id: Optional[str] = None` |
| `to_jsonl` | Execute to jsonl operation | `selector: str, mode: str = "text", soup_id: Optional[str] = None` |

## 📦 Dependencies

The following packages are required:
- `beautifulsoup4`
- `lxml`
- `html5lib`

## 🚀 Usage

This server is automatically discovered by the **MCP Host**. To run it manually:

```bash
uv run python -m mcp_servers.bs4_server.server
```
