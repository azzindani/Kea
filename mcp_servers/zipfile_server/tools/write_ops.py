import zipfile
import os


def create_new_zip(path: str, **kwargs) -> str:
    """Create empty zip."""
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED):
        pass
    return f"Created {path}"

def add_file(path: str, file_path: str, compression: str = "DEFLATED", **kwargs) -> str:
    """Add a local file to the zip."""
    cm = getattr(zipfile, f"ZIP_{compression.upper()}", zipfile.ZIP_DEFLATED)
    with zipfile.ZipFile(path, 'a', compression=cm) as zf:
        zf.write(file_path, arcname=os.path.basename(file_path))
    return f"Added {file_path}"

def add_file_as(path: str, file_path: str, arcname: str, **kwargs) -> str:
    """Add a local file but rename it inside zip."""
    with zipfile.ZipFile(path, 'a', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(file_path, arcname=arcname)
    return f"Added {file_path} as {arcname}"

def add_directory_recursive(path: str, dir_path: str, **kwargs) -> str:
    """Add entire folder structure."""
    count = 0
    with zipfile.ZipFile(path, 'a', compression=zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(dir_path))
                zf.write(file_path, arcname)
                count += 1
    return f"Added {count} files from {dir_path}"

def add_string_as_file(path: str, filename: str, content: str, **kwargs) -> str:
    """Create a file inside zip from a string (writestr)."""
    with zipfile.ZipFile(path, 'a', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(filename, content)
    return f"Wrote content to {filename}"

def append_file(path: str, file_path: str, **kwargs) -> str:
    """Append to existing zip (Alias for add_file)."""
    return add_file(path, file_path, **kwargs)

def write_py_zip(path: str, module_path: str, **kwargs) -> str:
    """Create PyZipFile (for packaging modules)."""
    with zipfile.PyZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writepy(module_path)
    return f"Packaged {module_path} into {path}"
