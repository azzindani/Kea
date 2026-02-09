import zipfile
import datetime
from typing import List, Dict, Any

def list_files(path: str, **kwargs) -> List[str]:
    """Get simple list of filenames in archive."""
    with zipfile.ZipFile(path, 'r') as zf:
        return zf.namelist()

def get_infolist_json(path: str, **kwargs) -> List[Dict[str, Any]]:
    """Get detailed info (size, compress_size, date) for all files."""
    results = []
    with zipfile.ZipFile(path, 'r') as zf:
        for info in zf.infolist():
            results.append({
                "filename": info.filename,
                "file_size": info.file_size,
                "compress_size": info.compress_size,
                "date_time": str(datetime.datetime(*info.date_time)),
                "CRC": info.CRC,
                "is_dir": info.is_dir()
            })
    return results

def get_file_info(path: str, member: str, **kwargs) -> Dict[str, Any]:
    """Get detailed info for specific file."""
    with zipfile.ZipFile(path, 'r') as zf:
        try:
            info = zf.getinfo(member)
            return {
                "filename": info.filename,
                "file_size": info.file_size,
                "compress_size": info.compress_size,
                "comment": info.comment.decode('utf-8', errors='replace'),
                "date_time": str(datetime.datetime(*info.date_time))
            }
        except KeyError:
            return {"error": "File not found in archive."}

def read_file_text(path: str, member: str, encoding: str = "utf-8", **kwargs) -> str:
    """Read content of a file as string."""
    with zipfile.ZipFile(path, 'r') as zf:
        try:
            with zf.open(member) as f:
                return f.read().decode(encoding)
        except KeyError:
            return "Error: File not found."
        except Exception as e:
            return f"Error reading: {e}"

def read_file_bytes(path: str, member: str, **kwargs) -> str:
    """Read content (returned as hex string representation)."""
    with zipfile.ZipFile(path, 'r') as zf:
        try:
            data = zf.read(member)
            return data.hex()[:1000] + "..." if len(data) > 1000 else data.hex()
        except Exception as e:
            return f"Error: {e}"

def get_file_size(path: str, member: str, **kwargs) -> int:
    """Uncompressed size."""
    with zipfile.ZipFile(path, 'r') as zf:
        return zf.getinfo(member).file_size

def get_compress_size(path: str, member: str, **kwargs) -> int:
    """Compressed size."""
    with zipfile.ZipFile(path, 'r') as zf:
        return zf.getinfo(member).compress_size

def get_date_time(path: str, member: str, **kwargs) -> str:
    """Modification time of inner file."""
    with zipfile.ZipFile(path, 'r') as zf:
        return str(datetime.datetime(*zf.getinfo(member).date_time))

def get_crc(path: str, member: str, **kwargs) -> int:
    """CRC32 checksum of inner file."""
    with zipfile.ZipFile(path, 'r') as zf:
        return zf.getinfo(member).CRC

def is_encrypted(path: str, member: str, **kwargs) -> bool:
    """Check if a file entry is encrypted (flag check)."""
    with zipfile.ZipFile(path, 'r') as zf:
        # Bit 0 of flag_bits indicates encryption
        return (zf.getinfo(member).flag_bits & 0x1) != 0
