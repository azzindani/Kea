
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
from mcp_servers.zipfile_server.tools import (
    core_ops, read_ops, extract_ops, write_ops, bulk_ops, super_ops
)
import structlog
from typing import Dict, Any, Optional, List, Tuple

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging import setup_logging
setup_logging()

mcp = FastMCP("zipfile_server", dependencies=["pandas"])

# ==========================================
# 1. Core
# ==========================================
# ==========================================
# 1. Core
# ==========================================
@mcp.tool()
def is_zipfile(path: str) -> bool: 
    """CHECKS if path is a valid zip file. [DATA]
    
    [RAG Context]
    """
    return core_ops.is_zipfile(path)

@mcp.tool()
def validate_archive(path: str) -> Dict[str, Any]: 
    """VALIDATES zip archive structure. [DATA]
    
    [RAG Context]
    Checks for corruption.
    """
    return core_ops.validate_archive(path)

@mcp.tool()
def get_zip_comment(path: str) -> str: 
    """READS zip archive comment. [DATA]
    
    [RAG Context]
    """
    return core_ops.get_zip_comment(path)

@mcp.tool()
def set_zip_comment(path: str, comment: str) -> str: 
    """WRITES zip archive comment. [ACTION]
    
    [RAG Context]
    """
    return core_ops.set_zip_comment(path, comment)

@mcp.tool()
def get_compression_type(path: str) -> Dict[str, str]: 
    """IDENTIFIES compression method. [DATA]
    
    [RAG Context]
    STORED, DEFLATED, BZIP2, LZMA.
    """
    return core_ops.get_compression_type(path)

@mcp.tool()
def check_integrity(path: str) -> Dict[str, Any]: 
    """TESTS zip file integrity. [DATA]
    
    [RAG Context]
    Verifies CRCs.
    """
    return core_ops.check_integrity(path)

# ==========================================
# 2. Read
# ==========================================
@mcp.tool()
def list_files(path: str) -> List[str]: 
    """LISTS files in zip archive. [DATA]
    
    [RAG Context]
    """
    return read_ops.list_files(path)

@mcp.tool()
def get_infolist_json(path: str) -> List[Dict[str, Any]]: 
    """GETS detailed file info list. [DATA]
    
    [RAG Context]
    JSON format.
    """
    return read_ops.get_infolist_json(path)

@mcp.tool()
def get_file_info(path: str, member: str) -> Dict[str, Any]: 
    """GETS info for specific file. [DATA]
    
    [RAG Context]
    """
    return read_ops.get_file_info(path, member)

@mcp.tool()
def read_file_text(path: str, member: str, encoding: str = "utf-8") -> str: 
    """READS text from zipped file. [DATA]
    
    [RAG Context]
    Decodes bytes to string.
    """
    return read_ops.read_file_text(path, member, encoding)

@mcp.tool()
def read_file_bytes(path: str, member: str) -> str: 
    """READS bytes from zipped file. [DATA]
    
    [RAG Context]
    Returns base64 encoded string.
    """
    return read_ops.read_file_bytes(path, member)

@mcp.tool()
def get_file_size(path: str, member: str) -> int: 
    """GETS uncompressed file size. [DATA]
    
    [RAG Context]
    """
    return read_ops.get_file_size(path, member)

@mcp.tool()
def get_compress_size(path: str, member: str) -> int: 
    """GETS compressed file size. [DATA]
    
    [RAG Context]
    """
    return read_ops.get_compress_size(path, member)

@mcp.tool()
def get_date_time(path: str, member: str) -> str: 
    """GETS file modification time. [DATA]
    
    [RAG Context]
    """
    return read_ops.get_date_time(path, member)

@mcp.tool()
def get_crc(path: str, member: str) -> int: 
    """GETS file CRC checksum. [DATA]
    
    [RAG Context]
    """
    return read_ops.get_crc(path, member)

@mcp.tool()
def is_encrypted(path: str, member: str) -> bool: 
    """CHECKS if file is encrypted. [DATA]
    
    [RAG Context]
    """
    return read_ops.is_encrypted(path, member)

# ==========================================
# 3. Extract
# ==========================================
# ==========================================
# 3. Extract
# ==========================================
@mcp.tool()
def extract_all(path: str, extract_path: str = "", pwd: Optional[str] = None) -> str: 
    """EXTRACTS all files from zip. [ACTION]
    
    [RAG Context]
    """
    if not extract_path:
        return "Error: No extraction path provided (extract_path)."
    return extract_ops.extract_all(path, extract_path, pwd)

@mcp.tool()
def extract_member(path: str, member: str, extract_path: str = "", pwd: Optional[str] = None) -> str: 
    """EXTRACTS single file from zip. [ACTION]
    
    [RAG Context]
    """
    if not extract_path:
        return "Error: No extraction path provided (extract_path)."
    return extract_ops.extract_member(path, member, extract_path, pwd)

@mcp.tool()
def extract_members_list(path: str, members: List[str], extract_path: str = "") -> str: 
    """EXTRACTS multiple files. [ACTION]
    
    [RAG Context]
    """
    if not extract_path:
        return "Error: No extraction path provided (extract_path)."
    return extract_ops.extract_members_list(path, members, extract_path)

@mcp.tool()
def extract_with_password(path: str, member: str, extract_path: str = "", pwd: str = "") -> str: 
    """EXTRACTS encrypted file. [ACTION]
    
    [RAG Context]
    """
    if not extract_path:
        return "Error: No extraction path provided (extract_path)."
    return extract_ops.extract_with_password(path, member, extract_path, pwd)

@mcp.tool()
def extract_by_pattern(path: str, pattern: str, extract_path: str = "") -> str: 
    """EXTRACTS files matching pattern. [ACTION]
    
    [RAG Context]
    Glob pattern.
    """
    if not extract_path:
        return "Error: No extraction path provided (extract_path)."
    return extract_ops.extract_by_pattern(path, pattern, extract_path)

@mcp.tool()
def extract_by_extension(path: str, extension: str, extract_path: str = "") -> str: 
    """EXTRACTS files by extension. [ACTION]
    
    [RAG Context]
    """
    if not extract_path:
        return "Error: No extraction path provided (extract_path)."
    return extract_ops.extract_by_extension(path, extension, extract_path)

@mcp.tool()
def safe_extract(path: str, extract_path: str = "") -> str: 
    """EXTRACTS verifying paths (Zip Slip). [ACTION]
    
    [RAG Context]
    Prevents path traversal attacks.
    """
    if not extract_path:
        return "Error: No extraction path provided (extract_path)."
    return extract_ops.safe_extract(path, extract_path)

# ==========================================
# 4. Write
# ==========================================
@mcp.tool()
def create_new_zip(path: str) -> str: 
    """CREATES new empty zip. [ACTION]
    
    [RAG Context]
    """
    return write_ops.create_new_zip(path)

@mcp.tool()
def add_file(path: str, file_path: str, compression: str = "DEFLATED") -> str: 
    """ADDS file to zip. [ACTION]
    
    [RAG Context]
    """
    return write_ops.add_file(path, file_path, compression)

@mcp.tool()
def add_file_as(path: str, file_path: str, arcname: str) -> str: 
    """ADDS file with new name. [ACTION]
    
    [RAG Context]
    """
    return write_ops.add_file_as(path, file_path, arcname)

@mcp.tool()
def add_directory_recursive(path: str, dir_path: str) -> str: 
    """ADDS directory recursively. [ACTION]
    
    [RAG Context]
    """
    return write_ops.add_directory_recursive(path, dir_path)

@mcp.tool()
def add_string_as_file(path: str, filename: str, content: str) -> str: 
    """ADDS string content as file. [ACTION]
    
    [RAG Context]
    """
    return write_ops.add_string_as_file(path, filename, content)

@mcp.tool()
def append_file(path: str, file_path: str) -> str: 
    """APPENDS file to existing zip. [ACTION]
    
    [RAG Context]
    """
    return write_ops.append_file(path, file_path)

@mcp.tool()
def write_py_zip(path: str, module_path: str) -> str: 
    """CREATES executable Python zip. [ACTION]
    
    [RAG Context]
    """
    return write_ops.write_py_zip(path, module_path)

# ==========================================
# 5. Bulk
# ==========================================
@mcp.tool()
def bulk_get_texts(path: str, members: List[str]) -> Dict[str, str]: 
    """READS text from multiple files. [DATA]
    
    [RAG Context]
    """
    return bulk_ops.bulk_get_texts(path, members)

@mcp.tool()
def bulk_add_files(path: str, file_paths: List[str]) -> str: 
    """ADDS multiple files to zip. [ACTION]
    
    [RAG Context]
    """
    return bulk_ops.bulk_add_files(path, file_paths)

@mcp.tool()
def bulk_validate_zips(paths: List[str]) -> Dict[str, str]: 
    """VALIDATES multiple zip files. [DATA]
    
    [RAG Context]
    """
    return bulk_ops.bulk_validate_zips(paths)

@mcp.tool()
def get_total_size(path: str) -> int: 
    """CALCULATES total uncompressed size. [DATA]
    
    [RAG Context]
    """
    return bulk_ops.get_total_size(path)

@mcp.tool()
def get_total_compressed_size(path: str) -> int: 
    """CALCULATES total compressed size. [DATA]
    
    [RAG Context]
    """
    return bulk_ops.get_total_compressed_size(path)

@mcp.tool()
def list_large_files(path: str, min_size: int) -> List[Dict[str, Any]]: 
    """LISTS files larger than size. [DATA]
    
    [RAG Context]
    """
    return bulk_ops.list_large_files(path, min_size)

# ==========================================
# 6. Super Tools
# ==========================================
@mcp.tool()
def merge_zip_files(zip1: str, zip2: str, output_zip: str) -> str: 
    """MERGES two zip files. [ACTION]
    
    [RAG Context]
    Combinines contents.
    """
    return super_ops.merge_zip_files(zip1, zip2, output_zip)

@mcp.tool()
def update_file_in_zip(zip_path: str, member: str, new_content: str) -> str: 
    """UPDATES content of file in zip. [ACTION]
    
    [RAG Context]
    """
    return super_ops.update_file_in_zip(zip_path, member, new_content)

@mcp.tool()
def delete_file_from_zip(zip_path: str, member: str) -> str: 
    """DELETES file from zip. [ACTION]
    
    [RAG Context]
    Recreates zip without file.
    """
    return super_ops.delete_file_from_zip(zip_path, member)

@mcp.tool()
def search_text_in_zip(path: str, keyword: str) -> List[str]: 
    """SEARCHES for text in zip files. [DATA]
    
    [RAG Context]
    Returns list of files containing keyword.
    """
    return super_ops.search_text_in_zip(path, keyword)

@mcp.tool()
def audit_security(path: str) -> Dict[str, Any]: 
    """CHECKS for security risks. [DATA]
    
    [RAG Context]
    Zip Slip, bombs, encrypted files.
    """
    return super_ops.audit_security(path)

@mcp.tool()
def convert_to_structure(path: str) -> Dict[str, Any]: 
    """CONVERTS zip to dictionary structure. [DATA]
    
    [RAG Context]
    Directory tree representation.
    """
    return super_ops.convert_to_structure(path)

@mcp.tool()
def backup_and_zip(dir_path: str) -> str: 
    """BACKUPS directory to zip. [ACTION]
    
    [RAG Context]
    Timestamped.
    """
    return super_ops.backup_and_zip(dir_path)

@mcp.tool()
def compare_zips(path1: str, path2: str) -> Dict[str, Any]: 
    """COMPARES content of two zips. [DATA]
    
    [RAG Context]
    Diff of files and sizes.
    """
    return super_ops.compare_zips(path1, path2)

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class ZipfileServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []
