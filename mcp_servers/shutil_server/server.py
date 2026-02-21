
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "mcp",
#   "pandas",
#   "structlog",
# ]
# ///

from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.shutil_server.tools import (
    core_ops, file_ops, dir_ops, archive_ops, bulk_ops, super_ops
)
import structlog
from typing import Dict, Any, Optional, List, Tuple

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging()

mcp = FastMCP("shutil_server", dependencies=["pandas"])

# ==========================================
# 1. Core
# ==========================================
# ==========================================
# 1. Core
# ==========================================
@mcp.tool()
def validate_path(path: str) -> bool: 
    """VALIDATES if path exists. [DATA]
    
    [RAG Context]
    """
    return core_ops.validate_path(path)

@mcp.tool()
def get_disk_usage(path: str) -> Dict[str, Any]: 
    """GETS disk usage statistics. [DATA]
    
    [RAG Context]
    Total, used, free space.
    """
    return core_ops.get_disk_usage(path)

@mcp.tool()
def which_command(cmd: str) -> Optional[str]: 
    """LOCATES executable in PATH. [DATA]
    
    [RAG Context]
    Like 'which' command.
    """
    return core_ops.which_command(cmd)

@mcp.tool()
def get_owner_info(path: str) -> Dict[str, Any]: 
    """GETS file owner information. [DATA]
    
    [RAG Context]
    UID, GID, User Name.
    """
    return core_ops.get_owner_info(path)

@mcp.tool()
def check_permissions(path: str) -> Dict[str, bool]: 
    """CHECKS file permissions. [DATA]
    
    [RAG Context]
    Read, Write, Execute.
    """
    return core_ops.check_permissions(path)

# ==========================================
# 2. File Operations
# ==========================================
@mcp.tool()
def copy_file(src: str, dst: str) -> str: 
    """COPIES a file (content + permissions). [ACTION]
    
    [RAG Context]
    Like `cp`.
    """
    return file_ops.copy_file(src, dst)

@mcp.tool()
def copy_file_2(src: str, dst: str) -> str: 
    """COPIES a file (preserves most metadata). [ACTION]
    
    [RAG Context]
    Like `cp -p`.
    """
    return file_ops.copy_file_2(src, dst)

@mcp.tool()
def copy_mode(src: str, dst: str) -> str: 
    """COPIES file permission bits only. [ACTION]
    
    [RAG Context]
    """
    return file_ops.copy_mode(src, dst)

@mcp.tool()
def copy_stat(src: str, dst: str) -> str: 
    """COPIES file metadata only. [ACTION]
    
    [RAG Context]
    Permissions, flags, times.
    """
    return file_ops.copy_stat(src, dst)

@mcp.tool()
def copy_file_content(src: str, dst: str) -> str: 
    """COPIES file content only. [ACTION]
    
    [RAG Context]
    """
    return file_ops.copy_file_content(src, dst)

@mcp.tool()
def move_file(src: str, dst: str) -> str: 
    """MOVES (entry) or RENAMES a file. [ACTION]
    
    [RAG Context]
    """
    return file_ops.move_file(src, dst)

@mcp.tool()
def change_ownership(path: str, user: Optional[str] = None, group: Optional[str] = None) -> str: 
    """CHANGES file ownership (chown). [ACTION]
    
    [RAG Context]
    """
    return file_ops.change_ownership(path, user, group)

@mcp.tool()
def touch_file(path: str) -> str: 
    """UPDATES timestamps or creates empty file. [ACTION]
    
    [RAG Context]
    """
    return file_ops.touch_file(path)

@mcp.tool()
def rename_file(src: str, dst: str) -> str: 
    """RENAMES a file within same directory. [ACTION]
    
    [RAG Context]
    """
    return file_ops.rename_file(src, dst)

# ==========================================
# 3. Directory Operations
# ==========================================
# ==========================================
# 3. Directory Operations
# ==========================================
@mcp.tool()
def copy_tree(src: str, dst: str) -> str: 
    """COPIES a directory tree efficiently. [ACTION]
    
    [RAG Context]
    Recursively copies an entire directory tree rooted at src to a directory named dst and returns the destination directory.
    """
    return dir_ops.copy_tree(src, dst)

@mcp.tool()
def copy_tree_dirs_exist(src: str, dst: str) -> str: 
    """COPIES tree allowing existing dirs. [ACTION]
    
    [RAG Context]
    Like copy_tree but allows dst to exist.
    """
    return dir_ops.copy_tree_dirs_exist(src, dst)

@mcp.tool()
def remove_tree(path: str) -> str: 
    """DELETES a directory tree (rm -rf). [ACTION]
    
    [RAG Context]
    """
    return dir_ops.remove_tree(path)

@mcp.tool()
def remove_tree_safe(path: str) -> str: 
    """DELETES directory tree safely. [ACTION]
    
    [RAG Context]
    Handles errors and permissions.
    """
    return dir_ops.remove_tree_safe(path)

@mcp.tool()
def move_directory(src: str, dst: str) -> str: 
    """MOVES a directory. [ACTION]
    
    [RAG Context]
    """
    return dir_ops.move_directory(src, dst)

@mcp.tool()
def count_files_recursive(path: str) -> int: 
    """COUNTS files recursively. [DATA]
    
    [RAG Context]
    """
    return dir_ops.count_files_recursive(path)

@mcp.tool()
def get_directory_size(path: str) -> int: 
    """CALCULATES directory size (bytes). [DATA]
    
    [RAG Context]
    """
    return dir_ops.get_directory_size(path)

@mcp.tool()
def list_directory_recursive(path: str) -> List[str]: 
    """LISTS all files recursively. [DATA]
    
    [RAG Context]
    """
    return dir_ops.list_directory_recursive(path)

@mcp.tool()
def clean_directory(path: str) -> str: 
    """EMTPTIES a directory. [ACTION]
    
    [RAG Context]
    Removes all content but keeps the directory.
    """
    return dir_ops.clean_directory(path)

# ==========================================
# 4. Archive Operations
# ==========================================
@mcp.tool()
def make_archive(base_name: str, format: str, root_dir: str) -> str: 
    """CREATES an archive file. [ACTION]
    
    [RAG Context]
    """
    return archive_ops.make_archive(base_name, format, root_dir)

@mcp.tool()
def unpack_archive(filename: str, extract_dir: str, format: str = None) -> str: 
    """EXTRACTS an archive file. [ACTION]
    
    [RAG Context]
    """
    return archive_ops.unpack_archive(filename, extract_dir, format)

@mcp.tool()
def get_archive_formats() -> List[Tuple[str, str]]: 
    """LISTS supported archive formats. [DATA]
    
    [RAG Context]
    """
    return archive_ops.get_archive_formats()

@mcp.tool()
def get_unpack_formats() -> List[Tuple[str, List[str], str]]: 
    """LISTS supported unpack formats. [DATA]
    
    [RAG Context]
    """
    return archive_ops.get_unpack_formats()

@mcp.tool()
def register_archive_format(name: str, function: Any, extra_args: List[Tuple[str, Any]] = None, description: str = "") -> str: 
    """REGISTERS new archive format. [ACTION]
    
    [RAG Context]
    """
    return archive_ops.register_archive_format(name, function, extra_args, description)

@mcp.tool()
def unregister_archive_format(name: str) -> str: 
    """UNREGISTERS archive format. [ACTION]
    
    [RAG Context]
    """
    return archive_ops.unregister_archive_format(name)

@mcp.tool()
def compress_directory(dir_path: str, archive_path: str) -> str: 
    """COMPRESSES directory to archive. [ACTION]
    
    [RAG Context]
    """
    return archive_ops.compress_directory(dir_path, archive_path)

# ==========================================
# 5. Bulk Operations
# ==========================================
@mcp.tool()
def bulk_copy_files(files: List[str], destination_dir: str) -> List[str]: 
    """COPIES multiple files. [ACTION]
    
    [RAG Context]
    """
    return bulk_ops.bulk_copy_files(files, destination_dir)

@mcp.tool()
def bulk_move_files(files: List[str], destination_dir: str) -> List[str]: 
    """MOVES multiple files. [ACTION]
    
    [RAG Context]
    """
    return bulk_ops.bulk_move_files(files, destination_dir)

@mcp.tool()
def bulk_delete_files(files: List[str]) -> List[str]: 
    """DELETES multiple files. [ACTION]
    
    [RAG Context]
    """
    return bulk_ops.bulk_delete_files(files)

@mcp.tool()
def bulk_rename_files(files: List[str], prefix: str = "", suffix: str = "") -> List[str]: 
    """RENAMES multiple files. [ACTION]
    
    [RAG Context]
    Adds prefix and/or suffix.
    """
    return bulk_ops.bulk_rename_files(files, prefix, suffix)

@mcp.tool()
def bulk_change_extension(files: List[str], new_extension: str) -> List[str]: 
    """CHANGES extension of multiple files. [ACTION]
    
    [RAG Context]
    """
    return bulk_ops.bulk_change_extension(files, new_extension)

@mcp.tool()
def copy_files_by_pattern(source_dir: str, pattern: str, destination_dir: str) -> List[str]: 
    """COPIES files matching pattern. [ACTION]
    
    [RAG Context]
    Glob pattern.
    """
    return bulk_ops.copy_files_by_pattern(source_dir, pattern, destination_dir)

@mcp.tool()
def move_files_by_pattern(source_dir: str, pattern: str, destination_dir: str) -> List[str]: 
    """MOVES files matching pattern. [ACTION]
    
    [RAG Context]
    Glob pattern.
    """
    return bulk_ops.move_files_by_pattern(source_dir, pattern, destination_dir)

@mcp.tool()
def delete_files_by_pattern(source_dir: str, pattern: str) -> List[str]: 
    """DELETES files matching pattern. [ACTION]
    
    [RAG Context]
    Glob pattern.
    """
    return bulk_ops.delete_files_by_pattern(source_dir, pattern)

# ==========================================
# 6. Super Tools
# ==========================================
@mcp.tool()
def synchronize_directories(src: str, dst: str) -> Dict[str, Any]: 
    """SYNCS two directories (rsync-like). [ACTION]
    
    [RAG Context]
    """
    return super_ops.synchronize_directories(src, dst)

@mcp.tool()
def backup_directory(path: str, backup_dir: str) -> str: 
    """CREATES timestamped backup. [ACTION]
    
    [RAG Context]
    """
    return super_ops.backup_directory(path, backup_dir)

@mcp.tool()
def safe_delete(files: List[str], trash_dir: str) -> List[str]: 
    """MOVES files to trash bin. [ACTION]
    
    [RAG Context]
    Safer than delete.
    """
    return super_ops.safe_delete(files, trash_dir)

@mcp.tool()
def organize_by_extension(directory: str) -> Dict[str, int]: 
    """ORGANIZES files by extension. [ACTION]
    
    [RAG Context]
    Moves files into subfolders (e.g. .jpg -> /images).
    """
    return super_ops.organize_by_extension(directory)

@mcp.tool()
def organize_by_date(directory: str) -> Dict[str, int]: 
    """ORGANIZES files by date. [ACTION]
    
    [RAG Context]
    Moves files into YYYY-MM-DD folders.
    """
    return super_ops.organize_by_date(directory)

@mcp.tool()
def deep_clean_temp(directory: str) -> List[str]: 
    """CLEANS temporary files. [ACTION]
    
    [RAG Context]
    Removes tmp, bak, log, etc.
    """
    return super_ops.deep_clean_temp(directory)

@mcp.tool()
def find_duplicates_and_act(directory: str, action: str = "report") -> Dict[str, Any]: 
    """FINDS and handles duplicate files. [ACTION]
    
    [RAG Context]
    Compares hash checksums.
    """
    return super_ops.find_duplicates_and_act(directory, action)

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class ShutilServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []
