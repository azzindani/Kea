# /// script
# dependencies = [
#   "mcp",
#   "pandas",
#   "structlog",
# ]
# ///

from mcp.server.fastmcp import FastMCP
from mcp_servers.shutil_server.tools import (
    core_ops, file_ops, dir_ops, archive_ops, bulk_ops, super_ops
)
import structlog
from typing import Dict, Any, Optional, List, Tuple

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("shutil_server", dependencies=["pandas"])

# ==========================================
# 1. Core
# ==========================================
@mcp.tool()
def validate_path(path: str) -> bool: return core_ops.validate_path(path)
@mcp.tool()
def get_disk_usage(path: str) -> Dict[str, Any]: return core_ops.get_disk_usage(path)
@mcp.tool()
def which_command(cmd: str) -> Optional[str]: return core_ops.which_command(cmd)
@mcp.tool()
def get_owner_info(path: str) -> Dict[str, Any]: return core_ops.get_owner_info(path)
@mcp.tool()
def check_permissions(path: str) -> Dict[str, bool]: return core_ops.check_permissions(path)

# ==========================================
# 2. File Operations
# ==========================================
@mcp.tool()
def copy_file(src: str, dst: str) -> str: return file_ops.copy_file(src, dst)
@mcp.tool()
def copy_file_2(src: str, dst: str) -> str: return file_ops.copy_file_2(src, dst)
@mcp.tool()
def copy_mode(src: str, dst: str) -> str: return file_ops.copy_mode(src, dst)
@mcp.tool()
def copy_stat(src: str, dst: str) -> str: return file_ops.copy_stat(src, dst)
@mcp.tool()
def copy_file_content(src: str, dst: str) -> str: return file_ops.copy_file_content(src, dst)
@mcp.tool()
def move_file(src: str, dst: str) -> str: return file_ops.move_file(src, dst)
@mcp.tool()
def change_ownership(path: str, user: Optional[str] = None, group: Optional[str] = None) -> str: return file_ops.change_ownership(path, user, group)
@mcp.tool()
def touch_file(path: str) -> str: return file_ops.touch_file(path)
@mcp.tool()
def rename_file(src: str, dst: str) -> str: return file_ops.rename_file(src, dst)

# ==========================================
# 3. Directory Operations
# ==========================================
@mcp.tool()
def copy_tree(src: str, dst: str) -> str: return dir_ops.copy_tree(src, dst)
@mcp.tool()
def copy_tree_dirs_exist(src: str, dst: str) -> str: return dir_ops.copy_tree_dirs_exist(src, dst)
@mcp.tool()
def remove_tree(path: str) -> str: return dir_ops.remove_tree(path)
@mcp.tool()
def remove_tree_safe(path: str) -> str: return dir_ops.remove_tree_safe(path)
@mcp.tool()
def move_directory(src: str, dst: str) -> str: return dir_ops.move_directory(src, dst)
@mcp.tool()
def count_files_recursive(path: str) -> int: return dir_ops.count_files_recursive(path)
@mcp.tool()
def get_directory_size(path: str) -> int: return dir_ops.get_directory_size(path)
@mcp.tool()
def list_directory_recursive(path: str) -> List[str]: return dir_ops.list_directory_recursive(path)
@mcp.tool()
def clean_directory(path: str) -> str: return dir_ops.clean_directory(path)

# ==========================================
# 4. Archive Operations
# ==========================================
@mcp.tool()
def make_archive(base_name: str, format: str, root_dir: str) -> str: return archive_ops.make_archive(base_name, format, root_dir)
@mcp.tool()
def unpack_archive(filename: str, extract_dir: str, format: str = None) -> str: return archive_ops.unpack_archive(filename, extract_dir, format)
@mcp.tool()
def get_archive_formats() -> List[Tuple[str, str]]: return archive_ops.get_archive_formats()
@mcp.tool()
def get_unpack_formats() -> List[Tuple[str, List[str], str]]: return archive_ops.get_unpack_formats()
@mcp.tool()
def register_archive_format(name: str, function: Any, extra_args: List[Tuple[str, Any]] = None, description: str = "") -> str: return archive_ops.register_archive_format(name, function, extra_args, description)
@mcp.tool()
def unregister_archive_format(name: str) -> str: return archive_ops.unregister_archive_format(name)
@mcp.tool()
def compress_directory(dir_path: str, archive_path: str) -> str: return archive_ops.compress_directory(dir_path, archive_path)

# ==========================================
# 5. Bulk Operations
# ==========================================
@mcp.tool()
def bulk_copy_files(files: List[str], destination_dir: str) -> List[str]: return bulk_ops.bulk_copy_files(files, destination_dir)
@mcp.tool()
def bulk_move_files(files: List[str], destination_dir: str) -> List[str]: return bulk_ops.bulk_move_files(files, destination_dir)
@mcp.tool()
def bulk_delete_files(files: List[str]) -> List[str]: return bulk_ops.bulk_delete_files(files)
@mcp.tool()
def bulk_rename_files(files: List[str], prefix: str = "", suffix: str = "") -> List[str]: return bulk_ops.bulk_rename_files(files, prefix, suffix)
@mcp.tool()
def bulk_change_extension(files: List[str], new_extension: str) -> List[str]: return bulk_ops.bulk_change_extension(files, new_extension)
@mcp.tool()
def copy_files_by_pattern(source_dir: str, pattern: str, destination_dir: str) -> List[str]: return bulk_ops.copy_files_by_pattern(source_dir, pattern, destination_dir)
@mcp.tool()
def move_files_by_pattern(source_dir: str, pattern: str, destination_dir: str) -> List[str]: return bulk_ops.move_files_by_pattern(source_dir, pattern, destination_dir)
@mcp.tool()
def delete_files_by_pattern(source_dir: str, pattern: str) -> List[str]: return bulk_ops.delete_files_by_pattern(source_dir, pattern)

# ==========================================
# 6. Super Tools
# ==========================================
@mcp.tool()
def synchronize_directories(src: str, dst: str) -> Dict[str, Any]: return super_ops.synchronize_directories(src, dst)
@mcp.tool()
def backup_directory(path: str, backup_dir: str) -> str: return super_ops.backup_directory(path, backup_dir)
@mcp.tool()
def safe_delete(files: List[str], trash_dir: str) -> List[str]: return super_ops.safe_delete(files, trash_dir)
@mcp.tool()
def organize_by_extension(directory: str) -> Dict[str, int]: return super_ops.organize_by_extension(directory)
@mcp.tool()
def organize_by_date(directory: str) -> Dict[str, int]: return super_ops.organize_by_date(directory)
@mcp.tool()
def deep_clean_temp(directory: str) -> List[str]: return super_ops.deep_clean_temp(directory)
@mcp.tool()
def find_duplicates_and_act(directory: str, action: str = "report") -> Dict[str, Any]: return super_ops.find_duplicates_and_act(directory, action)

if __name__ == "__main__":
    mcp.run()
