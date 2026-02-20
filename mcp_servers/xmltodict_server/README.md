# 🔌 Xmltodict Server

The `xmltodict_server` is an MCP server providing tools for **Xmltodict Server** functionality.
It is designed to be used within the Project ecosystem.

## 🧰 Tools

| Tool | Description | Arguments |
|:-----|:------------|:----------|
| `parse_xml_string` | Execute parse xml string operation | `xml_input: str` |
| `parse_xml_no_attrs` | Execute parse xml no attrs operation | `xml_input: str` |
| `parse_xml_no_namespaces` | Execute parse xml no namespaces operation | `xml_input: str` |
| `parse_xml_force_list` | Execute parse xml force list operation | `xml_input: str, tags: List[str]` |
| `parse_xml_force_cdata` | Execute parse xml force cdata operation | `xml_input: str` |
| `parse_xml_custom_encoding` | Execute parse xml custom encoding operation | `xml_input: str, encoding: str` |
| `parse_xml_disable_entities` | Execute parse xml disable entities operation | `xml_input: str` |
| `parse_xml_strip_whitespace` | Execute parse xml strip whitespace operation | `xml_input: str` |
| `parse_fragment` | Execute parse fragment operation | `xml_fragment: str` |
| `get_namespaces` | Execute get namespaces operation | `xml_input: str` |
| `unparse_dict_string` | Execute unparse dict string operation | `data: Dict[str, Any]` |
| `unparse_dict_pretty` | Execute unparse dict pretty operation | `data: Dict[str, Any]` |
| `unparse_dict_no_header` | Execute unparse dict no header operation | `data: Dict[str, Any]` |
| `unparse_dict_full_document` | Execute unparse dict full document operation | `data: Dict[str, Any]` |
| `unparse_dict_short_empty` | Execute unparse dict short empty operation | `data: Dict[str, Any]` |
| `dict_to_soap_envelope` | Execute dict to soap envelope operation | `data: Dict[str, Any]` |
| `dict_to_rss_xml` | Execute dict to rss xml operation | `data: Dict[str, Any]` |
| `dict_to_svg_xml` | Execute dict to svg xml operation | `data: Dict[str, Any]` |
| `read_xml_file` | Execute read xml file operation | `file_path: str` |
| `read_xml_file_no_attrs` | Execute read xml file no attrs operation | `file_path: str` |
| `read_xml_config` | Execute read xml config operation | `file_path: str` |
| `read_rss_feed` | Execute read rss feed operation | `file_path: str` |
| `read_atom_feed` | Execute read atom feed operation | `file_path: str` |
| `read_svg_file` | Execute read svg file operation | `file_path: str` |
| `scan_xml_structure` | Execute scan xml structure operation | `file_path: str` |
| `validate_well_formed` | Execute validate well formed operation | `file_path: str` |
| `write_xml_file` | Execute write xml file operation | `file_path: str, data: Dict[str, Any]` |
| `write_xml_file_pretty` | Execute write xml file pretty operation | `file_path: str, data: Dict[str, Any]` |
| `stream_xml_items` | Execute stream xml items operation | `file_path: str, item_depth: int = 2` |
| `count_tags_stream` | Execute count tags stream operation | `file_path: str, item_depth: int = 2` |
| `extract_tags_stream` | Execute extract tags stream operation | `file_path: str, tag_name: str, item_depth: int = 2` |
| `filter_xml_stream` | Execute filter xml stream operation | `file_path: str, key: str, value: str, item_depth: int = 2` |
| `stream_to_jsonl` | Execute stream to jsonl operation | `file_path: str, output_path: str, item_depth: int = 2` |
| `sample_xml_stream` | Execute sample xml stream operation | `file_path: str, limit: int = 100000, item_depth: int = 2` |
| `bulk_parse_strings` | Execute bulk parse strings operation | `xml_strings: List[str]` |
| `bulk_read_files` | Execute bulk read files operation | `file_paths: List[str]` |
| `convert_dir_xml_to_json` | Execute convert dir xml to json operation | `directory: str` |
| `convert_dir_json_to_xml` | Execute convert dir json to xml operation | `directory: str` |
| `merge_xml_files` | Execute merge xml files operation | `file_paths: List[str], root_name: str` |
| `grep_xml_dir` | Execute grep xml dir operation | `directory: str, search_text: str` |
| `xml_to_json_file` | Execute xml to json file operation | `xml_file: str, json_file: str` |
| `json_to_xml_file` | Execute json to xml file operation | `json_file: str, xml_file: str` |
| `diff_xml_files` | Execute diff xml files operation | `file_a: str, file_b: str` |
| `flatten_xml` | Execute flatten xml operation | `file_path: str` |
| `search_xml_path` | Execute search xml path operation | `file_path: str, path: str` |
| `mask_xml_sensitive` | Execute mask xml sensitive operation | `file_path: str, keys: List[str]` |
| `xml_to_csv_table` | Execute xml to csv table operation | `file_path: str, csv_path: str, item_key: str` |
| `reformat_xml_file` | Execute reformat xml file operation | `file_path: str` |
| `sanitize_xml_tags` | Execute sanitize xml tags operation | `file_path: str` |
| `generate_xsd_inference` | Execute generate xsd inference operation | `file_path: str` |
| `xml_heatmap` | Execute xml heatmap operation | `file_path: str` |

## 📦 Dependencies

Standard library only.

## 🚀 Usage

This server is automatically discovered by the **MCP Host**. To run it manually:

```bash
uv run python -m mcp_servers.xmltodict_server.server
```
