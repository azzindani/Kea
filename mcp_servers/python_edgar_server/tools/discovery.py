
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
            "sic": getattr(company, 'sic', 'N/A'),
            "sic_description": getattr(company, 'sic_description', 'N/A'),
            "fiscal_year_end": getattr(company, 'fiscal_year_end', 'N/A'),
            "state_of_incorporation": getattr(company, 'state_of_incorporation', 'N/A'),
            "mailing_address": str(company.mailing_address()) if hasattr(company, 'mailing_address') and callable(company.mailing_address) else str(getattr(company, 'mailing_address', None)),
            "business_address": str(company.business_address()) if hasattr(company, 'business_address') and callable(company.business_address) else str(getattr(company, 'business_address', None)),
            "phone": getattr(company, 'phone', 'N/A'),
            "ein": getattr(company, 'ein', 'N/A'),
            "tickers": getattr(company, 'tickers', []),
            "exchanges": getattr(company, 'exchanges', [])
        }
        
        # Recent Filings (Head 5)
        filings = company.get_filings()
        recent = []
        filing_list = filings.head(5)
        for filing in filing_list:
            recent.append({
                "form": filing.form,
                "date": str(filing.filing_date),
                "accession": filing.accession_number,
                "primary": filing.primary_document,
                "homepage_url": filing.homepage_url,
                "primary_document_url": filing.primary_document_url
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
        filings = company.get_filings(form=form) if form else company.get_filings()
        
        # Slice head
        filing_list = filings.head(limit)
        
        results = []
        for filing in filing_list:
            results.append({
                "form": filing.form,
                "date": str(filing.filing_date),
                "accession": filing.accession_number,
                "homepage_url": filing.homepage_url,
                "primary_document_url": filing.primary_document_url
            })
            
        return dict_to_result({"filings": results, "count": len(results)}, f"Filings: {ticker} {form or ''}")
        
    except Exception as e:
         return ToolResult(isError=True, content=[TextContent(text=str(e))])
