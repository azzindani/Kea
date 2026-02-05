
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.python_edgar_server.tools.core import EdgarCore, dict_to_result
import pandas as pd

async def get_fund_portfolio(arguments: dict) -> ToolResult:
    """
    Get detailed 13F portfolio for a fund (Institutional Manager).
    """
    try:
        ticker = arguments['ticker'] # Fund ticker (e.g. BRK-B) or CIK
        
        company = EdgarCore.get_company(ticker)
        
        # 1. Pandas Lookup
        filings = company.get_filings(form="13F-HR")
        df = filings.to_pandas()
        
        if df.empty: return dict_to_result([], "No 13F-HR found")
        
        acc = df.iloc[0]['accession_number']
        date = str(df.iloc[0]['filing_date'])
        
        # 2. Fetch
        # 13F objects in edgartools
        target_filings = company.get_filings(accession_number=acc)
        if not target_filings: return dict_to_result([], "Lookup failed")
        
        f = target_filings[0]
        obj = f.obj()
        
        # Table of holdings
        portfolio = []
        
        # obj.holdings or obj.table?
        data = None
        if hasattr(obj, 'holdings'): data = obj.holdings
        elif hasattr(obj, 'table'): data = obj.table
        
        if data is not None:
            if hasattr(data, 'to_dict'):
                portfolio = data.to_dict('records')
            elif isinstance(data, list):
                portfolio = data
                
        # Aggregate stats
        total_value = 0
        top_positions = []
        
        if portfolio:
            # Usually 'value' or 'valueOfHoldings' column
            # 'issuer' or 'nameOfIssuer'
            # Normalize
            normalized = []
            for p in portfolio:
                # auto-normalization
                name = p.get('nameOfIssuer') or p.get('issuer') or 'Unknown'
                # value in thousands usually?
                val = p.get('value') or p.get('valueOfHoldings') or 0
                ssh = p.get('sshPrnamt') or p.get('shares') or 0
                
                normalized.append({
                    "ticker": p.get('cusip', 'N/A'), # 13F often has CUSIP not ticker
                    "name": name,
                    "value": val,
                    "shares": ssh
                })
                try:
                    total_value += float(val)
                except: pass
            
            # Sort by value
            normalized.sort(key=lambda x: float(x['value']), reverse=True)
            top_positions = normalized[:50]
        
        return dict_to_result({
            "fund": ticker,
            "filing_date": date,
            "top_holdings": top_positions,
            "total_value_reported": total_value,
            "entries_count": len(portfolio)
        }, f"Fund Portfolio ({date})")
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
