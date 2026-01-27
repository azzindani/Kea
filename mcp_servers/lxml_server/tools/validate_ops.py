from lxml import etree, isoschematron
import os
from io import BytesIO

def validate_dtd(xml_input: str, dtd_input: str) -> str:
    """Validate against DTD string."""
    try:
        dtd = etree.DTD(BytesIO(dtd_input.encode('utf-8')))
        root = etree.fromstring(xml_input.encode('utf-8'))
        if dtd.validate(root):
            return "Valid"
        return f"Invalid: {dtd.error_log.filter_from_errors()}"
    except Exception as e:
        return f"Error: {e}"

def validate_xsd(xml_input: str, xsd_input: str) -> str:
    """Validate against XSD string."""
    try:
        schema_doc = etree.fromstring(xsd_input.encode('utf-8'))
        schema = etree.XMLSchema(schema_doc)
        doc = etree.fromstring(xml_input.encode('utf-8'))
        if schema.validate(doc):
            return "Valid"
        return f"Invalid: {schema.error_log}"
    except Exception as e:
        return f"Error: {e}"

def validate_relaxng(xml_input: str, rng_input: str) -> str:
    """Validate against RelaxNG string."""
    try:
        rng_doc = etree.fromstring(rng_input.encode('utf-8'))
        rng = etree.RelaxNG(rng_doc)
        doc = etree.fromstring(xml_input.encode('utf-8'))
        if rng.validate(doc):
            return "Valid"
        return f"Invalid: {rng.error_log}"
    except Exception as e:
        return f"Error: {e}"

def validate_schematron(xml_input: str, schema_input: str) -> str:
    """Validate against Schematron."""
    try:
        s_doc = etree.fromstring(schema_input.encode('utf-8'))
        s = isoschematron.Schematron(s_doc)
        doc = etree.fromstring(xml_input.encode('utf-8'))
        if s.validate(doc):
            return "Valid"
        return f"Invalid: {s.error_log}"
    except Exception as e:
        return f"Error: {e}"

def check_well_formed(xml_input: str) -> bool:
    try:
        etree.fromstring(xml_input.encode('utf-8'))
        return True
    except:
        return False
