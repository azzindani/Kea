# 🔌 Shutil Server

The `shutil_server` is an MCP server providing tools for **Shutil Server** functionality.
It is designed to be used within the Kea ecosystem.

## 🧰 Tools

| Tool | Description | Arguments |
|:-----|:------------|:----------|
| `validate_path` | Execute validate path operation | `path: str` |
| `get_disk_usage` | Execute get disk usage operation | `path: str` |
| `which_command` | Execute which command operation | `cmd: str` |
| `get_owner_info` | Execute get owner info operation | `path: str` |
| `check_permissions` | Execute check permissions operation | `path: str` |
| `copy_file` | Execute copy file operation | `src: str, dst: str` |
| `copy_file_2` | Execute copy file 2 operation | `src: str, dst: str` |
| `copy_mode` | Execute copy mode operation | `src: str, dst: str` |
| `copy_stat` | Execute copy stat operation | `src: str, dst: str` |
| `copy_file_content` | Execute copy file content operation | `src: str, dst: str` |
| `move_file` | Execute move file operation | `src: str, dst: str` |
| `change_ownership` | Execute change ownership operation | `path: str, user: Optional[str] = None, group: Optional[str] = None` |
| `touch_file` | Execute touch file operation | `path: str` |
| `rename_file` | Execute rename file operation | `src: str, dst: str` |
| `copy_tree` | Execute copy tree operation | `src: str, dst: str` |
| `copy_tree_dirs_exist` | Execute copy tree dirs exist operation | `src: str, dst: str` |
| `remove_tree` | Execute remove tree operation | `path: str` |
| `remove_tree_safe` | Execute remove tree safe operation | `path: str` |
| `move_directory` | Execute move directory operation | `src: str, dst: str` |
| `count_files_recursive` | Execute count files recursive operation | `path: str` |
| `get_directory_size` | Execute get directory size operation | `path: str` |
| `list_directory_recursive` | Execute list directory recursive operation | `path: str` |
| `clean_directory` | Execute clean directory operation | `path: str` |
| `make_archive` | Execute make archive operation | `base_name: str, format: str, root_dir: str` |
| `unpack_archive` | Execute unpack archive operation | `filename: str, extract_dir: str, format: str = None` |
| `get_archive_formats` | Execute get archive formats operation | `` |
| `get_unpack_formats` | Execute get unpack formats operation | `` |
| `register_archive_format` | Execute register archive format operation | `name: str, function: Any, extra_args: List[Tuple[str, Any]] = None, description: str = ""` |
| `unregister_archive_format` | Execute unregister archive format operation | `name: str` |
| `compress_directory` | Execute compress directory operation | `dir_path: str, archive_path: str` |
| `bulk_copy_files` | Execute bulk copy files operation | `files: List[str], destination_dir: str` |
| `bulk_move_files` | Execute bulk move files operation | `files: List[str], destination_dir: str` |
| `bulk_delete_files` | Execute bulk delete files operation | `files: List[str]` |
| `bulk_rename_files` | Execute bulk rename files operation | `files: List[str], prefix: str = "", suffix: str = ""` |
| `bulk_change_extension` | Execute bulk change extension operation | `files: List[str], new_extension: str` |
| `copy_files_by_pattern` | Execute copy files by pattern operation | `source_dir: str, pattern: str, destination_dir: str` |
| `move_files_by_pattern` | Execute move files by pattern operation | `source_dir: str, pattern: str, destination_dir: str` |
| `delete_files_by_pattern` | Execute delete files by pattern operation | `source_dir: str, pattern: str` |
| `synchronize_directories` | Execute synchronize directories operation | `src: str, dst: str` |
| `backup_directory` | Execute backup directory operation | `path: str, backup_dir: str` |
| `safe_delete` | Execute safe delete operation | `files: List[str], trash_dir: str` |
| `organize_by_extension` | Execute organize by extension operation | `directory: str` |
| `organize_by_date` | Execute organize by date operation | `directory: str` |
| `deep_clean_temp` | Execute deep clean temp operation | `directory: str` |
| `find_duplicates_and_act` | Execute find duplicates and act operation | `directory: str, action: str = "report"` |

## 📦 Dependencies

The following packages are required:
- `pandas`

## 🚀 Usage

This server is automatically discovered by the **MCP Host**. To run it manually:

```bash
uv run python -m mcp_servers.shutil_server.server
```
