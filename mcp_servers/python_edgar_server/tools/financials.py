
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.python_edgar_server.tools.core import EdgarCore, dict_to_result
import asyncio

async def get_financial_statements(arguments: dict) -> ToolResult:
    """
    Get specialized financials (Income, Balance, CashFlow).
    Args:
        ticker: str
        statement: "Income", "Balance", "CashFlow"
    """
    try:
        ticker = arguments['ticker']
        statement = arguments.get('statement', 'Income')
        
        company = EdgarCore.get_company(ticker)
        
        # Try Aggregated Financials first
        data = None
        try:
            financials = company.financials
            if financials:
                if "Income" in statement: data = financials.income_statement
                elif "Balance" in statement: data = financials.balance_sheet
                elif "Cash" in statement: data = financials.cash_flow_statement
        except Exception:
            # Fallback: Get latest 10-K
            filings = company.get_filings(form="10-K")
            df = filings.to_pandas()
            if not df.empty:
                acc = df.iloc[0]['accession_number']
                f_objs = company.get_filings(accession=acc)
                if f_objs:
                    # Filing financials
                    # filing.financials might exist? No, usually filing.obj() -> XBRL
                    # or filing.xbrl()
                    pass
        
        if data is not None:
             # Check if dataframe or custom object
            if hasattr(data, 'to_dict'):
                # Reshape for JSON
                # If it's a dataframe, to_dict("split") or "records" might be better
                # Default to_dict() is {col: {index: val}}
                try:
                    res = data.to_dict() 
                    return dict_to_result(res, f"{statement} Statement")
                except:
                    return dict_to_result({"raw": str(data)}, f"{statement} Statement")
            else:
                return dict_to_result({"raw": str(data)}, f"{statement} Statement")
        
        return dict_to_result({}, "Statement not found via Aggregation")
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_key_metrics(arguments: dict) -> ToolResult:
    """
    Get key XBRL metrics (Revenue, Net Income) history.
    """
    try:
        ticker = arguments['ticker']
        company = EdgarCore.get_company(ticker)
        
        # Try income statement
        try:
            inc = company.financials.income_statement
            if inc is not None:
                # Convert to string/dict and let user parse or extract specific known rows
                # Limit size
                df = inc
                if hasattr(df, 'head'): df = df.head(10) # Columns are periods
                return dict_to_result({"metrics": str(df)}, "Key Metrics Available")
        except:
            pass
            
        return dict_to_result({}, "No Financials found")
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
