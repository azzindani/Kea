from lxml import etree
import os
import glob
from typing import List, Dict, Any

def iterparse_counts(file_path: str, tag: str) -> int:
    """Count tags via streaming (low memory)."""
    try:
        count = 0
        context = etree.iterparse(file_path, events=("end",), tag=tag)
        for _, elem in context:
            count += 1
            # Clear element to free memory
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]
        return count
    except Exception:
        return -1

def iterparse_extract(file_path: str, tag: str, limit: int = 20) -> List[str]:
    """Extract specific subtrees via streaming."""
    try:
        items = []
        context = etree.iterparse(file_path, events=("end",), tag=tag)
        for _, elem in context:
            items.append(etree.tostring(elem, encoding='unicode', pretty_print=True))
            elem.clear()
            while elem.getprevious() is not None:
                 del elem.getparent()[0]
            if len(items) >= limit:
                break
        return items
    except Exception as e:
        return [f"Error: {e}"]

def bulk_xpath_files(directory: str, xpath: str, extension: str = "*.xml") -> Dict[str, List[str]]:
    """Run XPath across directory of files."""
    results = {}
    files = glob.glob(os.path.join(directory, extension))
    for f in files:
        try:
           doc = etree.parse(f)
           matches = doc.xpath(xpath)
           # Helper to convert matches
           str_matches = []
           for m in matches:
               if hasattr(m, "tag"):
                   str_matches.append(etree.tostring(m, encoding='unicode'))
               else:
                   str_matches.append(str(m))
           if str_matches:
               results[f] = str_matches
        except:
            pass
    return results

def bulk_validate_xsd(directory: str, xsd_path: str) -> Dict[str, str]:
    """Validate directory against XSD."""
    try:
        schema = etree.XMLSchema(etree.parse(xsd_path))
    except Exception as e:
        return {"error": f"Invalid XSD: {e}"}
        
    results = {}
    files = glob.glob(os.path.join(directory, "*.xml"))
    for f in files:
        try:
            doc = etree.parse(f)
            if schema.validate(doc):
                results[f] = "Valid"
            else:
                results[f] = "Invalid"
        except Exception as e:
            results[f] = f"Error: {e}"
    return results

def bulk_transform_xslt(directory: str, xslt_path: str, output_dir: str) -> str:
    """Apply XSLT to directory."""
    try:
        xslt = etree.XSLT(etree.parse(xslt_path))
        if not os.path.exists(output_dir): os.makedirs(output_dir)
        count = 0
        
        files = glob.glob(os.path.join(directory, "*.xml"))
        for f in files:
            try:
                doc = etree.parse(f)
                new_doc = xslt(doc)
                filename = os.path.basename(f)
                with open(os.path.join(output_dir, filename), 'wb') as fout:
                    fout.write(etree.tostring(new_doc, pretty_print=True))
                count += 1
            except: pass
        return f"Transformed {count} files to {output_dir}"
    except Exception as e:
        return f"Error: {e}"

def grep_elements_dir(directory: str, search_text: str) -> Dict[str, List[str]]:
    """Find elements containing text in dir."""
    results = {}
    xpath = f"//*[contains(text(), '{search_text}')]"
    files = glob.glob(os.path.join(directory, "*.xml"))
    for f in files:
        try:
            doc = etree.parse(f)
            matches = doc.xpath(xpath)
            if matches:
                results[f] = [etree.tostring(m, encoding='unicode') for m in matches[:5]]
        except: pass
    return results

def map_xml_structure(directory: str) -> Dict[str, str]:
    """Generate simple structure map for dir (Root tag)."""
    results = {}
    files = glob.glob(os.path.join(directory, "*.xml"))
    for f in files:
        try:
            # Iterparse just start event to get root tag fast
            context = etree.iterparse(f, events=("start",))
            _, root = next(context)
            results[f] = root.tag
        except:
             results[f] = "Error"
    return results
