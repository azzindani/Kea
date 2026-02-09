import zipfile
import shutil
import os
import datetime
from typing import List, Dict, Any

def merge_zip_files(zip1: str, zip2: str, output_zip: str, **kwargs) -> str:
    """Combine Zip A and Zip B into Zip C."""
    with zipfile.ZipFile(output_zip, 'w', compression=zipfile.ZIP_DEFLATED) as z_out:
        # Copy zip1
        with zipfile.ZipFile(zip1, 'r') as z1:
            for item in z1.infolist():
                z_out.writestr(item, z1.read(item.filename))
        # Copy zip2
        with zipfile.ZipFile(zip2, 'r') as z2:
            for item in z2.infolist():
                z_out.writestr(item, z2.read(item.filename))
    return f"Merged {zip1} and {zip2} into {output_zip}"

def update_file_in_zip(zip_path: str, member: str, new_content: str, **kwargs) -> str:
    """'Edit' a file (Read all -> Write new Zip with replaced content)."""
    temp_zip = zip_path + ".temp"
    try:
        with zipfile.ZipFile(zip_path, 'r') as z_in:
            with zipfile.ZipFile(temp_zip, 'w', compression=zipfile.ZIP_DEFLATED) as z_out:
                for item in z_in.infolist():
                    if item.filename != member:
                        z_out.writestr(item, z_in.read(item.filename))
                    else:
                        z_out.writestr(member, new_content)
        shutil.move(temp_zip, zip_path)
        return f"Updated {member} in {zip_path}"
    except Exception as e:
        if os.path.exists(temp_zip): os.remove(temp_zip)
        return f"Error: {e}"

def delete_file_from_zip(zip_path: str, member: str, **kwargs) -> str:
    """'Delete' (Read all -> Write new Zip excluding target)."""
    temp_zip = zip_path + ".temp"
    try:
        with zipfile.ZipFile(zip_path, 'r') as z_in:
            with zipfile.ZipFile(temp_zip, 'w', compression=zipfile.ZIP_DEFLATED) as z_out:
                for item in z_in.infolist():
                    if item.filename != member:
                        z_out.writestr(item, z_in.read(item.filename))
        shutil.move(temp_zip, zip_path)
        return f"Deleted {member} from {zip_path}"
    except Exception as e:
        if os.path.exists(temp_zip): os.remove(temp_zip)
        return f"Error: {e}"

def search_text_in_zip(path: str, keyword: str, **kwargs) -> List[str]:
    """Search for string content across all files in zip."""
    matches = []
    with zipfile.ZipFile(path, 'r') as zf:
        for member in zf.namelist():
            try:
                # Only check reasonably sized files?
                # For now search all
                with zf.open(member) as f:
                    content = f.read().decode('utf-8', errors='ignore')
                    if keyword in content:
                        matches.append(member)
            except:
                pass
    return matches

def audit_security(path: str, **kwargs) -> Dict[str, Any]:
    """Check for Zip Bombs (compression ratio) and Zip Slip paths."""
    issues = []
    with zipfile.ZipFile(path, 'r') as zf:
        for info in zf.infolist():
            # Zip Slip
            if ".." in info.filename or info.filename.startswith("/"):
                issues.append(f"Zip Slip Risk: {info.filename}")
            
            # Zip Bomb (Ratio > 100)
            if info.compress_size > 0 and (info.file_size / info.compress_size) > 100:
                issues.append(f"High Compression (Bomb Risk?): {info.filename}")
                
    return {
        "safe": len(issues) == 0,
        "issues": issues
    }

def convert_to_structure(path: str, **kwargs) -> Dict[str, Any]:
    """Return JSON tree structure of zip content."""
    tree = {}
    with zipfile.ZipFile(path, 'r') as zf:
        for f in zf.namelist():
            parts = f.strip("/").split("/")
            current = tree
            for part in parts:
                if part not in current:
                    current[part] = {}
                current = current[part]
    return tree

def backup_and_zip(dir_path: str, **kwargs) -> str:
    """Copy folder, Zip it, timestamp it."""
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_name = f"{os.path.basename(dir_path)}_backup_{ts}"
    shutil.make_archive(out_name, 'zip', dir_path)
    return f"Created {out_name}.zip"

def compare_zips(path1: str, path2: str, **kwargs) -> Dict[str, Any]:
    """Compare file lists and CRCs of two zips."""
    def get_sigs(p):
        with zipfile.ZipFile(p, 'r') as z:
            return {i.filename: i.CRC for i in z.infolist()}
            
    sigs1 = get_sigs(path1)
    sigs2 = get_sigs(path2)
    
    only_in_1 = set(sigs1.keys()) - set(sigs2.keys())
    only_in_2 = set(sigs2.keys()) - set(sigs1.keys())
    diff_crc = {k: (sigs1[k], sigs2[k]) for k in sigs1 if k in sigs2 and sigs1[k] != sigs2[k]}
    
    return {
        "unique_to_1": list(only_in_1),
        "unique_to_2": list(only_in_2),
        "different_content": list(diff_crc.keys())
    }
