
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.python_edgar_server.tools.core import EdgarCore, dict_to_result
import pandas as pd

async def get_insider_trades(arguments: dict) -> ToolResult:
    """
    Get recent insider trades (Form 4) for a ticker.
    Returns: List of transactions.
    """
    try:
        ticker = arguments['ticker']
        limit = arguments.get('limit', 5) # Number of *filings* to parse
        
        company = EdgarCore.get_company(ticker)
        
        # 1. Get List via Pandas (Robust)
        all_filings = company.get_filings(form="4")
        df = all_filings.to_pandas()
        
        if df.empty:
            return dict_to_result([], "No Form 4s")
            
        # 2. Iterate Top N Accessions
        # Safe pattern: Get accession from DF, then lookup single filing object
        targets_df = df.head(limit)
        
        all_txs = []
        
        for _, row in targets_df.iterrows():
            try:
                acc = row['accession_number']
                
                # Fetch single filing safe lookup
                # Note: get_filings(accession=...) returns a Filings container, take [0]
                target_filings = company.get_filings(accession_number=acc)
                if not target_filings: continue
                
                f = target_filings[0]
                
                # Parse
                obj = f.obj()
                if hasattr(obj, 'transactions') and obj.transactions is not None:
                    tx_df = obj.transactions
                    if hasattr(tx_df, 'to_dict'):
                        records = tx_df.to_dict('records')
                        for r in records:
                            r['filing_date'] = str(f.filing_date)
                            r['accession'] = f.accession_no
                            # Clean nan
                            clean_r = {k: v for k, v in r.items() if pd.notna(v)}
                            all_txs.append(clean_r)
            except Exception:
                continue
                
        return dict_to_result(all_txs, f"Insider Trades ({len(all_txs)})")
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_institutional_holdings(arguments: dict) -> ToolResult:
    """
    Get 13F holdings (if available).
    """
    try:
        ticker = arguments['ticker'] # Usually a fund ticker like BRK-B? Or CIK?
        
        company = EdgarCore.get_company(ticker)
        
        # 1. Pandas Lookup
        all_filings = company.get_filings(form="13F-HR")
        df = all_filings.to_pandas()
        
        if df.empty: return dict_to_result([], "No 13F-HR found")
        
        # Get latest
        acc = df.iloc[0]['accession_number']
        
        # 2. Safe Fetch
        filings = company.get_filings(accession_number=acc)
        if not filings: return dict_to_result([], "Lookup failed")
        
        latest = filings[0]
        obj = latest.obj()
        
        # obj.holdings or obj.table?
        # edgartools 13F object usually has a table property
        data = None
        if hasattr(obj, 'holdings'): data = obj.holdings
        elif hasattr(obj, 'table'): data = obj.table
        
        if data is not None:
             if hasattr(data, 'head'): data = data.head(100) # Limit
             if hasattr(data, 'to_dict'):
                 return dict_to_result(data.to_dict('records'), "13F Holdings (Top 100)")
                 
        return dict_to_result({"raw": str(obj)}, "13F found but table extraction unsure")
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
