
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.python_edgar_server.tools.core import EdgarCore, dict_to_result
import asyncio

async def analyze_company_profile(arguments: dict) -> ToolResult:
    """
    Get comprehensive profile for a company (Facts, Filings, Financials summary).
    Input: ticker.
    """
    try:
        ticker = arguments['ticker']
        company = EdgarCore.get_company(ticker)
        
        info = {
            "ticker": ticker,
            "cik": company.cik,
            "name": company.name,
            "industry": getattr(company, 'industry', 'N/A'),
        }
        
        # Recent Filings via Pandas
        filings = company.get_filings()
        df = filings.to_pandas()
        
        # Head 5
        recent = []
        # Check DataFrame columns (accession_number vs accession_no) usually accession_number in pandas
        for idx, row in df.head(5).iterrows():
            recent.append({
                "form": row.get('form'),
                "date": str(row.get('filing_date')),
                "accession": row.get('accession_number'),
                "primary": row.get('primary_document')
            })
            
        info['recent_filings'] = recent
        
        return dict_to_result(info, f"Company Profile: {ticker}")
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def find_filings(arguments: dict) -> ToolResult:
    """
    Search for filings.
    Args:
        ticker: str
        form: str (e.g. "10-K")
        limit: int
    """
    try:
        ticker = arguments.get('ticker')
        form = arguments.get('form')
        limit = arguments.get('limit', 10)
        
        company = EdgarCore.get_company(ticker)
        # Form filter in get_filings might still be safe?
        filings = company.get_filings(form=form) if form else company.get_filings()
        
        df = filings.to_pandas()
        # Slice head
        df = df.head(limit)
        
        results = []
        for idx, row in df.iterrows():
            results.append({
                "form": row.get('form'),
                "date": str(row.get('filing_date')),
                "accession": row.get('accession_number')
            })
            
        return dict_to_result({"filings": results, "count": len(results)}, f"Filings: {ticker} {form or ''}")
        
    except Exception as e:
         return ToolResult(isError=True, content=[TextContent(text=str(e))])
