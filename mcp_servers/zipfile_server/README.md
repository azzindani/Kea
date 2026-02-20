# 🔌 Zipfile Server

The `zipfile_server` is an MCP server providing tools for **Zipfile Server** functionality.
It is designed to be used within the Project ecosystem.

## 🧰 Tools

| Tool | Description | Arguments |
|:-----|:------------|:----------|
| `is_zipfile` | Execute is zipfile operation | `path: str` |
| `validate_archive` | Execute validate archive operation | `path: str` |
| `get_zip_comment` | Execute get zip comment operation | `path: str` |
| `set_zip_comment` | Execute set zip comment operation | `path: str, comment: str` |
| `get_compression_type` | Execute get compression type operation | `path: str` |
| `check_integrity` | Execute check integrity operation | `path: str` |
| `list_files` | Execute list files operation | `path: str` |
| `get_infolist_json` | Execute get infolist json operation | `path: str` |
| `get_file_info` | Execute get file info operation | `path: str, member: str` |
| `read_file_text` | Execute read file text operation | `path: str, member: str, encoding: str = "utf-8"` |
| `read_file_bytes` | Execute read file bytes operation | `path: str, member: str` |
| `get_file_size` | Execute get file size operation | `path: str, member: str` |
| `get_compress_size` | Execute get compress size operation | `path: str, member: str` |
| `get_date_time` | Execute get date time operation | `path: str, member: str` |
| `get_crc` | Execute get crc operation | `path: str, member: str` |
| `is_encrypted` | Execute is encrypted operation | `path: str, member: str` |
| `extract_all` | Execute extract all operation | `path: str, extract_path: str, pwd: Optional[str] = None` |
| `extract_member` | Execute extract member operation | `path: str, member: str, extract_path: str, pwd: Optional[str] = None` |
| `extract_members_list` | Execute extract members list operation | `path: str, members: List[str], extract_path: str` |
| `extract_with_password` | Execute extract with password operation | `path: str, member: str, extract_path: str, pwd: str` |
| `extract_by_pattern` | Execute extract by pattern operation | `path: str, pattern: str, extract_path: str` |
| `extract_by_extension` | Execute extract by extension operation | `path: str, extension: str, extract_path: str` |
| `safe_extract` | Execute safe extract operation | `path: str, extract_path: str` |
| `create_new_zip` | Execute create new zip operation | `path: str` |
| `add_file` | Execute add file operation | `path: str, file_path: str, compression: str = "DEFLATED"` |
| `add_file_as` | Execute add file as operation | `path: str, file_path: str, arcname: str` |
| `add_directory_recursive` | Execute add directory recursive operation | `path: str, dir_path: str` |
| `add_string_as_file` | Execute add string as file operation | `path: str, filename: str, content: str` |
| `append_file` | Execute append file operation | `path: str, file_path: str` |
| `write_py_zip` | Execute write py zip operation | `path: str, module_path: str` |
| `bulk_get_texts` | Execute bulk get texts operation | `path: str, members: List[str]` |
| `bulk_add_files` | Execute bulk add files operation | `path: str, file_paths: List[str]` |
| `bulk_validate_zips` | Execute bulk validate zips operation | `paths: List[str]` |
| `get_total_size` | Execute get total size operation | `path: str` |
| `get_total_compressed_size` | Execute get total compressed size operation | `path: str` |
| `list_large_files` | Execute list large files operation | `path: str, min_size: int` |
| `merge_zip_files` | Execute merge zip files operation | `zip1: str, zip2: str, output_zip: str` |
| `update_file_in_zip` | Execute update file in zip operation | `zip_path: str, member: str, new_content: str` |
| `delete_file_from_zip` | Execute delete file from zip operation | `zip_path: str, member: str` |
| `search_text_in_zip` | Execute search text in zip operation | `path: str, keyword: str` |
| `audit_security` | Execute audit security operation | `path: str` |
| `convert_to_structure` | Execute convert to structure operation | `path: str` |
| `backup_and_zip` | Execute backup and zip operation | `dir_path: str` |
| `compare_zips` | Execute compare zips operation | `path1: str, path2: str` |

## 📦 Dependencies

The following packages are required:
- `pandas`

## 🚀 Usage

This server is automatically discovered by the **MCP Host**. To run it manually:

```bash
uv run python -m mcp_servers.zipfile_server.server
```
