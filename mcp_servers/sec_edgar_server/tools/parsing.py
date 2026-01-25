
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.sec_edgar_server.tools.core import dict_to_result
import os

async def extract_filing_metadata(arguments: dict) -> ToolResult:
    """
    Parse the SGML Header of a downloaded SEC filing.
    Extracts: Accession, Period, Date, Company, CIK, Form Type.
    Args:
        path: Absolute path to the .txt file.
    """
    try:
        path = arguments['path']
        if not os.path.exists(path):
             return ToolResult(isError=True, content=[TextContent(text="File not found.")])
        
        metadata = {}
        # Read just the first 100 lines usually contains the header
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            header_lines = []
            for _ in range(200):
                line = f.readline()
                if not line: break
                header_lines.append(line.strip())
                if "</SEC-HEADER>" in line: break
                
        # Parse SGML-like lines
        # Examples:
        # CONFORMED SUBMISSION TYPE:	10-K
        # COMPANY CONFORMED NAME:	APPLE INC
        # CENTRAL INDEX KEY:	0000320193
        # STANDARD INDUSTRIAL CLASSIFICATION:	ELECTRONIC COMPUTERS [3571]
        # FILED AS OF DATE:	20231103
        # CONFORMED PERIOD OF REPORT:	20230930
        
        for line in header_lines:
            if ":" in line:
                parts = line.split(":", 1)
                key = parts[0].strip()
                val = parts[1].strip()
                
                if key == "ACCESSION NUMBER": metadata['accession_number'] = val
                elif key == "CONFORMED SUBMISSION TYPE": metadata['form_type'] = val
                elif key == "COMPANY CONFORMED NAME": metadata['company_name'] = val
                elif key == "CENTRAL INDEX KEY": metadata['cik'] = val
                elif key == "FILED AS OF DATE": metadata['filed_date'] = val
                elif key == "CONFORMED PERIOD OF REPORT": metadata['period_of_report'] = val
                elif key == "FISCAL YEAR END": metadata['fiscal_year_end'] = val
                elif key == "Standard Industrial Classification": metadata['sic'] = val
                
        metadata['file_path'] = path
        return dict_to_result(metadata, "Filing Metadata")
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
