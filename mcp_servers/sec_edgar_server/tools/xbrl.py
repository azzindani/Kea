
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.sec_edgar_server.tools.core import dict_to_result
import os
import re
import glob

async def extract_xbrl_financials(arguments: dict) -> ToolResult:
    """
    Extract key financial metrics from XBRL files (.xml) in a folder.
    Args:
        folder_path: Path to the specific filing folder (containing .xml).
    """
    try:
        folder = arguments['folder_path']
        if not os.path.exists(folder):
             return ToolResult(isError=True, content=[TextContent(text="Folder not found.")])
        
        # Find XML files (usually ends in _htm.xml or _lab.xml or just .xml)
        # We want the 'instance' document, often has ticker-date.xml
        xml_files = glob.glob(os.path.join(folder, "*.xml"))
        
        # skip xsd, pre, lab, cal, def usually. We want the instance.
        instance_files = [f for f in xml_files if not any(x in f for x in ["_pre.xml", "_lab.xml", "_cal.xml", "_def.xml"])]
        
        if not instance_files:
             return dict_to_result({"found": False, "note": "No Instance XML found. Did you use download_filing_details?"}, "XBRL Extraction")
             
        target_xml = instance_files[0]
        with open(target_xml, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Regex extraction for common US-GAAP tags
        # Format: <us-gaap:NetIncomeLoss ...>123456</us-gaap:NetIncomeLoss>
        # Or <us-gaap:Revenue ...>
        
        metrics = {}
        
        # Define patterns
        targets = {
            "Revenues": [r"Revenues", r"RevenueFromContractWithCustomerExcludingAssessedTax"],
            "NetIncome": [r"NetIncomeLoss", r"ProfitLoss"],
            "Assets": [r"Assets"],
            "Liabilities": [r"Liabilities"],
            "StockholdersEquity": [r"StockholdersEquity"],
            "Cash": [r"CashAndCashEquivalentsAtCarryingValue"]
        }
        
        for key, patterns in targets.items():
            for pat in patterns:
                # Regex: <us-gaap:Pattern ... >VALUE</...>
                # Handle namespaces and attributes
                # <([a-zA-Z0-9]+:)?Pattern.*?>(.*?)</
                regex = rf"<([a-zA-Z0-9]+:)?{pat}[^>]*>(.*?)</"
                matches = re.findall(regex, content, re.IGNORECASE | re.DOTALL)
                
                if matches:
                    # Collect values (there might be contextRefs for different years)
                    # For simplicity, returning list of raw values found
                    # Cleaning: remove newlines
                    values = [m[1].strip() for m in matches]
                    # Filter distinct
                    values = list(set(values))
                    if key not in metrics: metrics[key] = []
                    metrics[key].extend(values)
                    
        return dict_to_result({
            "file": os.path.basename(target_xml),
            "financials": metrics,
            "note": "Raw XBRL values. Context/Units (millions/billions) depend on ContextRef."
        }, "XBRL Financials")
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
