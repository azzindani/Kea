
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.python_edgar_server.tools.core import EdgarCore, dict_to_result
import pandas as pd

async def get_filing_section_content(arguments: dict) -> ToolResult:
    """
    Get text of a specific section (e.g., 'Item 1A', 'Item 7').
    """
    try:
        ticker = arguments['ticker']
        form = arguments.get('form', '10-K')
        item = arguments['item'] # e.g. "Item 1A"
        
        company = EdgarCore.get_company(ticker)
        
        # Accession lookup pattern for stability
        filings = company.get_filings(form=form)
        df = filings.to_pandas()
        if df.empty: return dict_to_result({}, "No filing")
        acc = df.iloc[0]['accession_number']
        
        targets = company.get_filings(accession_number=acc)
        f = targets[0]
        
        obj = f.obj()
        if not obj: return dict_to_result({}, "Parse failed")
        
        content = None
        # obj[item]? or obj.items[item]?
        # edgartools TenK object usually implements __getitem__
        try:
            content = obj[item]
        except:
            if hasattr(obj, 'items'):
                content = obj.items.get(item)
                
        if not content:
             return dict_to_result({"items_available": str(list(obj.items.keys())) if hasattr(obj,'items') else []}, f"Item '{item}' not found")
             
        return dict_to_result({"item": item, "content": str(content)[:50000]}, "Section Content")
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
