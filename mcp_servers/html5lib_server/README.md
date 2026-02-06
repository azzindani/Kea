# 🔌 Html5Lib Server

The `html5lib_server` is an MCP server providing tools for **Html5Lib Server** functionality.
It is designed to be used within the Kea ecosystem.

## 🧰 Tools

| Tool | Description | Arguments |
|:-----|:------------|:----------|
| `parse_string` | Execute parse string operation | `html_input: str` |
| `parse_fragment` | Execute parse fragment operation | `html_input: str` |
| `parse_lxml` | Execute parse lxml operation | `html_input: str` |
| `parse_dom` | Execute parse dom operation | `html_input: str` |
| `parse_validating` | Execute parse validating operation | `html_input: str` |
| `parse_file` | Execute parse file operation | `file_path: str` |
| `parser_errors` | Execute parser errors operation | `html_input: str` |
| `detect_encoding` | Execute detect encoding operation | `file_path: str` |
| `walk_tree_print` | Execute walk tree print operation | `html_input: str` |
| `walk_get_tokens` | Execute walk get tokens operation | `html_input: str, limit: int = 100000` |
| `walk_find_tags` | Execute walk find tags operation | `html_input: str, tag_name: str` |
| `walk_extract_text` | Execute walk extract text operation | `html_input: str` |
| `count_tokens` | Execute count tokens operation | `html_input: str` |
| `lint_stream` | Execute lint stream operation | `html_input: str` |
| `serialize_tree` | Execute serialize tree operation | `html_input: str` |
| `serialize_minidom` | Execute serialize minidom operation | `html_input: str` |
| `serialize_pretty` | Execute serialize pretty operation | `html_input: str` |
| `serialize_no_whitespace` | Execute serialize no whitespace operation | `html_input: str` |
| `serialize_inject_meta` | Execute serialize inject meta operation | `html_input: str` |
| `reencode_html` | Execute reencode html operation | `html_input: str, encoding: str` |
| `sanitize_html` | Execute sanitize html operation | `html_input: str` |
| `filter_whitespace` | Execute filter whitespace operation | `html_input: str` |
| `filter_optional_tags` | Execute filter optional tags operation | `html_input: str` |
| `filter_comments` | Execute filter comments operation | `html_input: str` |
| `filter_inject_token` | Execute filter inject token operation | `html_input: str, token_type: str, name: str` |
| `escape_html_entities` | Execute escape html entities operation | `text: str` |
| `alphabetical_attributes` | Execute alphabetical attributes operation | `html_input: str` |
| `bulk_parse_validate` | Execute bulk parse validate operation | `directory: str` |
| `bulk_sanitize_dir` | Execute bulk sanitize dir operation | `directory: str, output_dir: str` |
| `bulk_extract_text` | Execute bulk extract text operation | `directory: str` |
| `bulk_convert_encoding` | Execute bulk convert encoding operation | `directory: str, target_encoding: str = "utf-8"` |
| `grep_html_tokens` | Execute grep html tokens operation | `directory: str, token_name: str` |
| `parse_benchmarks` | Execute parse benchmarks operation | `file_size_mb: int = 1` |
| `repair_html_page` | Execute repair html page operation | `html_input: str` |
| `html_diff_token` | Execute html diff token operation | `html_a: str, html_b: str` |
| `table_extractor_resilient` | Execute table extractor resilient operation | `html_input: str` |
| `visualize_dom_tree` | Execute visualize dom tree operation | `html_input: str` |
| `extract_links_stream` | Execute extract links stream operation | `html_input: str` |
| `convert_html_to_valid_xml` | Execute convert html to valid xml operation | `html_input: str` |
| `tree_adapter_bridge` | Execute tree adapter bridge operation | `html_input: str, target: str = 'dom'` |
| `inspect_treebuilder_options` | Execute inspect treebuilder options operation | `` |
| `memory_usage_estimate` | Execute memory usage estimate operation | `html_input: str` |
| `profile_page_structure` | Execute profile page structure operation | `html_input: str` |
| `generate_toc_from_html` | Execute generate toc from html operation | `html_input: str` |
| `html_minify_aggressive` | Execute html minify aggressive operation | `html_input: str` |
| `extract_metadata` | Execute extract metadata operation | `html_input: str` |
| `inject_script_tag` | Execute inject script tag operation | `html_input: str, script_src: str` |
| `remove_elements_by_class` | Execute remove elements by class operation | `html_input: str, class_name: str` |
| `highlight_text` | Execute highlight text operation | `html_input: str, text: str` |
| `auto_close_tags` | Execute auto close tags operation | `html_input: str` |
| `simulate_browser_parse` | Execute simulate browser parse operation | `html_input: str` |
| `stream_to_json` | Execute stream to json operation | `html_input: str` |
| `debug_encoding_sniff` | Execute debug encoding sniff operation | `bytes_input: bytes` |
| `merge_html_fragments` | Execute merge html fragments operation | `fragments: List[str]` |
| `split_html_sections` | Execute split html sections operation | `html_input: str` |
| `validate_doctype` | Execute validate doctype operation | `html_input: str` |
| `html5_conformance_check` | Execute html5 conformance check operation | `html_input: str` |
| `anonymize_text_content` | Execute anonymize text content operation | `html_input: str` |

## 📦 Dependencies

Standard library only.

## 🚀 Usage

This server is automatically discovered by the **MCP Host**. To run it manually:

```bash
uv run python -m mcp_servers.html5lib_server.server
```
