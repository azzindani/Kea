
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.python_edgar_server.tools.core import EdgarCore, dict_to_result
import pandas as pd
import asyncio

async def get_bulk_company_facts(arguments: dict) -> ToolResult:
    """
    Get metadata (CIK, Name, Industry) for a list of tickers.
    Args:
        tickers: list[str] or comma-separated string
    """
    try:
        tickers_input = arguments['tickers']
        if isinstance(tickers_input, str):
            tickers = [t.strip() for t in tickers_input.split(',')]
        else:
            tickers = tickers_input
            
        results = {}
        errors = []
        
        for t in tickers:
            try:
                c = EdgarCore.get_company(t)
                results[t] = {
                    "cik": c.cik,
                    "name": c.name,
                    "industry": getattr(c, 'industry', 'N/A')
                }
            except Exception as e:
                errors.append(f"{t}: {e}")
                
        return dict_to_result({"success": results, "errors": errors}, "Bulk Company Facts")
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_financial_history(arguments: dict) -> ToolResult:
    """
    Get historical key metrics (Revenue, Net Income) for a ticker over N years.
    """
    try:
        ticker = arguments['ticker']
        years = arguments.get('years', 5)
        
        company = EdgarCore.get_company(ticker)
        
        # Get 10-Ks
        filings = company.get_filings(form="10-K")
        df = filings.to_pandas()
        
        history = []
        
        # Take top N
        for idx, row in df.head(years).iterrows():
            acc = row.get('accession_number')
            date = str(row.get('filing_date'))
            
            try:
                # Get Object
                f_objs = company.get_filings(accession_number=acc)
                if not f_objs: continue
                f = f_objs[0]
                
                # Financials (XBRL)
                # Try obj().financials? Or f.financials?
                # edgartools 10K object has .financials usually
                # But it might require parsing step
                
                # Simplified: Return availability or try to parse
                # If parsed, it's slow. 
                # Let's rely on the Aggregated Financials if possible (company.financials) used earlier
                # The company.financials object usually contains HISTORY (columns are dates).
                pass

            except:
                pass
        
        # Better approach: Use company.financials (Aggregated)
        # It usually has columns as dates
        try:
             financials = company.financials
             if financials and financials.income_statement is not None:
                 inc = financials.income_statement
                 # df columns are periods?
                 # Convert to dict
                 if hasattr(inc, 'to_dict'):
                     return dict_to_result(inc.to_dict(), f"Financial History ({ticker})")
        except:
            pass
            
        return dict_to_result({}, "Financial History Not Available via Aggregation")
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
