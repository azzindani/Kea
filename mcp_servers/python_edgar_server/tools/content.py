
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.python_edgar_server.tools.core import EdgarCore, dict_to_result
import asyncio

async def get_filing_text(arguments: dict) -> ToolResult:
    """
    Get text content of the latest filing of a specific type.
    """
    try:
        ticker = arguments['ticker']
        form = arguments['form']
        
        company = EdgarCore.get_company(ticker)
        
        # 1. Find Accession via Pandas (safest)
        all_filings = company.get_filings(form=form)
        df = all_filings.to_pandas()
        
        if df.empty:
            return dict_to_result({}, "No filing found")
            
        # Get latest accession
        acc = df.iloc[0]['accession_number']
        
        # 2. Get Single Filing Object
        filings = company.get_filings(accession_number=acc)
        if not filings: return dict_to_result({}, "Filing lookup failed")
        
        filing = filings[0]
        
        # .markdown()
        md = filing.markdown()
        if not md: md = ""
        
        return ToolResult(content=[TextContent(text=md[:50000])]) # Cap size
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_filing_sections(arguments: dict) -> ToolResult:
    """
    Get available sections (Items) in a filing.
    """
    try:
        ticker = arguments['ticker']
        form = arguments.get('form', '10-K')
        
        company = EdgarCore.get_company(ticker)
        
        # 1. Accession Lookup
        all_filings = company.get_filings(form=form)
        df = all_filings.to_pandas()
        if df.empty: return dict_to_result({}, "No filings.")
        
        acc = df.iloc[0]['accession_number']
        
        # 2. Get Object
        filings = company.get_filings(accession_number=acc)
        filing = filings[0]
        
        # filing.obj()
        obj = filing.obj()
        if not obj:
             return dict_to_result({}, "Parsing not supported for this filing")
             
        sections = []
        if hasattr(obj, 'items'):
            if isinstance(obj.items, dict): sections = list(obj.items.keys())
            elif isinstance(obj.items, list): sections = [str(i) for i in obj.items] 
            else: sections = ["Unknown structure"]
            
        return dict_to_result({
            "sections": sections,
            "homepage_url": filing.homepage_url,
            "primary_document_url": filing.primary_document_url
        }, "Filing Sections")
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
