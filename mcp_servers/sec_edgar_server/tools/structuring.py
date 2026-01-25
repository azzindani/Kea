
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.sec_edgar_server.tools.core import dict_to_result
import os
import re
import xml.etree.ElementTree as ET

def _extract_xml_block(content):
    # Find XML block. Usually <XML> ... </XML>
    # There might be multiple. 13F usually has a primary HTML and an informational table XML.
    # Look for <informationTable> inside XML or <ownershipDocument>
    
    # Simple regex for XML tags
    # <XML> ... </XML>
    matches = re.findall(r'<XML>(.*?)</XML>', content, re.DOTALL | re.IGNORECASE)
    return matches

async def parse_13f_holdings(arguments: dict) -> ToolResult:
    """
    Parse 13F-HR text file to extract holdings.
    Returns: List of holdings (Issuer, CUSIP, Value, Shares).
    """
    try:
        path = arguments['path']
        if not os.path.exists(path):
             return ToolResult(isError=True, content=[TextContent(text="File not found.")])
             
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        xml_blocks = _extract_xml_block(content)
        holdings = []
        found_table = False
        
        for block in xml_blocks:
            if "informationTable" in block:
                try:
                    # Clean the block (sometimes has newlines/whitespace)
                    root = ET.fromstring(block.strip())
                    
                    # Namespace handling might be needed. 
                    # Usually: {http://www.sec.gov/edgar/document/thirteenf/informationtable}
                    # We can strip namespaces for simplicity or use specific finds
                    for info in root.findall(".//*[nameOfIssuer].."): # Find parent of nameOfIssuer?
                        # Better: Iterate all 'infoTable' elements
                        # Since namespace varies, let's use regex for extracting rows to be robust against schema versions
                        pass
                        
                    # Let's try Regex approach on the block because namespace parsing in ElementTree without known map is painful
                    # Iterate <infoTable> ... </infoTable>
                    rows = re.findall(r'<infoTable>(.*?)</infoTable>', block, re.DOTALL)
                    for row in rows:
                        issuer = re.search(r'<nameOfIssuer>(.*?)</nameOfIssuer>', row)
                        cusip = re.search(r'<cusip>(.*?)</cusip>', row)
                        value = re.search(r'<value>(.*?)</value>', row)
                        ssh = re.search(r'<sshPrnamt>(.*?)</sshPrnamt>', row)
                        
                        holdings.append({
                            "issuer": issuer.group(1) if issuer else None,
                            "cusip": cusip.group(1) if cusip else None,
                            "value": value.group(1) if value else None,
                            "shares": ssh.group(1) if ssh else None
                        })
                    found_table = True
                    break # Usually only one info table
                except Exception as e:
                    return dict_to_result({"error": str(e)}, "XML Parse Error")

        if not found_table:
            return dict_to_result([], "No 13F Information Table Found (Check if 13F-NT?)")
            
        # Limit result size
        return dict_to_result(holdings[:500], f"13F Holdings ({len(holdings)} positions)")
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def parse_form4_transactions(arguments: dict) -> ToolResult:
    """
    Parse Form 4 (Insider Trading) XML.
    Returns: List of non-derivative transactions.
    """
    try:
        path = arguments['path']
        if not os.path.exists(path): return ToolResult(isError=True, content=[TextContent(text="File not found.")])
        with open(path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()
        
        xml_blocks = _extract_xml_block(content)
        txs = []
        
        for block in xml_blocks:
            if "ownershipDocument" in block:
                # Regex for <nonDerivativeTransaction>
                items = re.findall(r'<nonDerivativeTransaction>(.*?)</nonDerivativeTransaction>', block, re.DOTALL)
                for item in items:
                    date = re.search(r'<transactionDate>.*?<value>(.*?)</value>', item, re.DOTALL)
                    code = re.search(r'<transactionCoding>.*?<transactionCode>(.*?)</transactionCode>', item, re.DOTALL)
                    shares = re.search(r'<transactionAmounts>.*?<transactionShares>.*?<value>(.*?)</value>', item, re.DOTALL)
                    price = re.search(r'<transactionPricePerShare>.*?<value>(.*?)</value>', item, re.DOTALL)
                    acquired = re.search(r'<transactionAcquiredDisposedCode>.*?<value>(.*?)</value>', item, re.DOTALL)
                    
                    txs.append({
                        "date": date.group(1) if date else None,
                        "code": code.group(1) if code else None,
                        "shares": shares.group(1) if shares else None,
                        "price": price.group(1) if price else None,
                        "type": acquired.group(1) if acquired else None # A=Acquire, D=Dispose
                    })
                break
                
        return dict_to_result(txs, f"Insider Transactions ({len(txs)})")
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
