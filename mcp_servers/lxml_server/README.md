# 🔌 Lxml Server

The `lxml_server` is an MCP server providing tools for **Lxml Server** functionality.
It is designed to be used within the Project ecosystem.

## 🧰 Tools

| Tool | Description | Arguments |
|:-----|:------------|:----------|
| `parse_xml_string` | Execute parse xml string operation | `xml_input: str` |
| `parse_html_string` | Execute parse html string operation | `html_input: str` |
| `parse_file` | Execute parse file operation | `file_path: str` |
| `parse_xml_recover` | Execute parse xml recover operation | `xml_input: str` |
| `to_string` | Execute to string operation | `xml_input: str` |
| `to_pretty_string` | Execute to pretty string operation | `xml_input: str` |
| `strip_tags` | Execute strip tags operation | `xml_input: str, tags: List[str]` |
| `strip_elements` | Execute strip elements operation | `xml_input: str, tags: List[str]` |
| `get_element_text` | Execute get element text operation | `xml_input: str, xpath: str = "."` |
| `get_element_attrs` | Execute get element attrs operation | `xml_input: str, xpath: str = "."` |
| `xpath_query` | Execute xpath query operation | `xml_input: str, query: str` |
| `xpath_query_text` | Execute xpath query text operation | `xml_input: str, query: str` |
| `xpath_query_attr` | Execute xpath query attr operation | `xml_input: str, query: str` |
| `css_select` | Execute css select operation | `xml_input: str, selector: str` |
| `get_parent` | Execute get parent operation | `xml_input: str, xpath: str` |
| `get_children` | Execute get children operation | `xml_input: str, xpath: str` |
| `get_siblings` | Execute get siblings operation | `xml_input: str, xpath: str` |
| `xslt_transform` | Execute xslt transform operation | `xml_input: str, xslt_input: str` |
| `clean_html` | Execute clean html operation | `html_input: str` |
| `make_links_absolute` | Execute make links absolute operation | `html_input: str, base_url: str` |
| `remove_javascript` | Execute remove javascript operation | `html_input: str` |
| `builder_create` | Execute builder create operation | `tag: str, text: str, **attrs` |
| `add_child` | Execute add child operation | `xml_input: str, parent_xpath: str, child_tag: str, child_text: str` |
| `set_attribute` | Execute set attribute operation | `xml_input: str, xpath: str, key: str, value: str` |
| `remove_attribute` | Execute remove attribute operation | `xml_input: str, xpath: str, key: str` |
| `replace_element` | Execute replace element operation | `xml_input: str, xpath: str, new_tag: str` |
| `validate_dtd` | Execute validate dtd operation | `xml_input: str, dtd_input: str` |
| `validate_xsd` | Execute validate xsd operation | `xml_input: str, xsd_input: str` |
| `validate_relaxng` | Execute validate relaxng operation | `xml_input: str, rng_input: str` |
| `validate_schematron` | Execute validate schematron operation | `xml_input: str, schema_input: str` |
| `check_well_formed` | Execute check well formed operation | `xml_input: str` |
| `objectify_parse` | Execute objectify parse operation | `xml_input: str` |
| `objectify_dump` | Execute objectify dump operation | `xml_input: str` |
| `data_element_create` | Execute data element create operation | `value: Any, type_annotation: str = None` |
| `iterparse_counts` | Execute iterparse counts operation | `file_path: str, tag: str` |
| `iterparse_extract` | Execute iterparse extract operation | `file_path: str, tag: str, limit: int = 100000` |
| `bulk_xpath_files` | Execute bulk xpath files operation | `directory: str, xpath: str, extension: str = "*.xml"` |
| `bulk_validate_xsd` | Execute bulk validate xsd operation | `directory: str, xsd_path: str` |
| `bulk_transform_xslt` | Execute bulk transform xslt operation | `directory: str, xslt_path: str, output_dir: str` |
| `grep_elements_dir` | Execute grep elements dir operation | `directory: str, search_text: str` |
| `map_xml_structure` | Execute map xml structure operation | `directory: str` |
| `html_table_to_json` | Execute html table to json operation | `html_input: str` |
| `web_scraper_simple` | Execute web scraper simple operation | `url: str, xpath: str` |
| `diff_xml_trees` | Execute diff xml trees operation | `xml_a: str, xml_b: str` |
| `merge_xml_trees` | Execute merge xml trees operation | `xml_strings: List[str], root_tag: str = "merged"` |
| `xml_to_dict_lxml` | Execute xml to dict lxml operation | `xml_input: str` |
| `dict_to_xml_lxml` | Execute dict to xml lxml operation | `json_input: str` |
| `extract_links_bulk` | Execute extract links bulk operation | `directory: str` |
| `auto_fix_html` | Execute auto fix html operation | `html_input: str` |
| `generate_rss_item` | Execute generate rss item operation | `title: str, link: str, desc: str` |
| `xinclude_process` | Execute xinclude process operation | `xml_input: str` |
| `visualize_tree_structure` | Execute visualize tree structure operation | `xml_input: str` |
| `minify_xml` | Execute minify xml operation | `xml_input: str` |
| `benchmark_parsing` | Execute benchmark parsing operation | `file_size_mb: int = 10` |
| `anonymize_xml_content` | Execute anonymize xml content operation | `xml_input: str` |

## 📦 Dependencies

Standard library only.

## 🚀 Usage

This server is automatically discovered by the **MCP Host**. To run it manually:

```bash
uv run python -m mcp_servers.lxml_server.server
```
