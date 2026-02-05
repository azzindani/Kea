
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.python_edgar_server.tools.core import EdgarCore, dict_to_result
import pandas as pd

async def get_xbrl_tag_values(arguments: dict) -> ToolResult:
    """
    Get historical values for a specific US-GAAP tag (e.g., 'StockBasedCompensation', 'ResearchAndDevelopmentExpense').
    Returns a time-series of values.
    """
    try:
        ticker = arguments['ticker']
        tag = arguments['tag'] # e.g. "StockBasedCompensation"
        taxonomy = arguments.get('taxonomy', 'us-gaap')
        
        company = EdgarCore.get_company(ticker)
        
        # get_facts() fetches the company facts JSON (API based, usually stable)
        facts = company.get_facts()
        
        if not facts:
            return dict_to_result({}, "No facts found")
            
        # Manual iteration since facts is an iterable of FinancialFact
        # and doesn't support to_pandas() directly in this version
        filtered_facts = []
        
        # Check if facts is iterable
        for f in facts:
            # f is FinancialFact
            # Attributes: usually .fact property
            # Fallback: Parse string rep if attribute missing
            
            extracted_tag = None
            extracted_val = 0
            extracted_date = 'N/A'
            extracted_units = 'N/A'
            extracted_form = 'N/A'
            
            # 1. Try Attribute Access
            if hasattr(f, 'fact'):
                extracted_tag = f.fact
                extracted_val = getattr(f, 'val', getattr(f, 'value', 0))
                extracted_date = str(getattr(f, 'end', 'N/A'))
                extracted_units = getattr(f, 'units', getattr(f, 'unit', 'N/A'))
                extracted_form = getattr(f, 'form', 'N/A')
            else:
                # 2. String Parsing Fallback
                # Format: FinancialFact(dei:EntityCommonStockSharesOutstanding=895,816,758, ...)
                s = str(f)
                if '(' in s and '=' in s:
                    try:
                        # "FinancialFact(dei:Tag=Val"
                        content = s.split('(', 1)[1]
                        tag_part = content.split('=', 1)[0]
                        extracted_tag = tag_part
                        
                        # Attempt to get value/date from attributes even if fact attr missing
                        extracted_val = getattr(f, 'val', getattr(f, 'value', 0))
                        extracted_date = str(getattr(f, 'end', 'N/A'))
                    except: pass
            
            if extracted_tag:
                # Handle namespaced tags e.g. "us-gaap:ResearchAndDevelopmentExpense"
                # We want to match "ResearchAndDevelopmentExpense"
                raw_tag = extracted_tag
                clean_tag = raw_tag.split(':')[-1] if ':' in raw_tag else raw_tag
                
                if clean_tag.lower() == tag.lower() or raw_tag.lower() == tag.lower():
                     filtered_facts.append({
                        "date": extracted_date,
                        "value": extracted_val,
                        "form": extracted_form,
                        "units": extracted_units
                    })
                raw_tag = f.fact
                clean_tag = raw_tag.split(':')[-1] if ':' in raw_tag else raw_tag
                
                if clean_tag == tag or raw_tag == tag:
                    filtered_facts.append({
                        "date": str(getattr(f, 'end', 'N/A')),
                        "value": getattr(f, 'val', getattr(f, 'value', 0)),
                        "form": getattr(f, 'form', 'N/A'),
                        "units": getattr(f, 'units', getattr(f, 'unit', 'N/A'))
                    })
        
        if not filtered_facts:
            # Try case insensitive search or list avail
            # Since we can't easily list all unique tags without iterating all
            return dict_to_result([], f"Tag '{tag}' not found in facts.")
            
        # Sort by date descending
        filtered_facts.sort(key=lambda x: x['date'], reverse=True)
            
        return dict_to_result(filtered_facts[:50], f"History for {tag}")
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def search_xbrl_tags(arguments: dict) -> ToolResult:
    """
    Search for available XBRL tags for a company.
    """
    try:
        ticker = arguments['ticker']
        query = arguments.get('query', '').lower()
        
        company = EdgarCore.get_company(ticker)
        facts = company.get_facts()
        
        if not facts: return dict_to_result([], "No facts")
        
        # Manual unique tags collection
        unique_tags = set()
        for f in facts:
            t = None
            if hasattr(f, 'fact'): t = f.fact
            else:
                 # Fallback
                 s = str(f)
                 if '(' in s and '=' in s:
                     try:
                         t = s.split('(', 1)[1].split('=', 1)[0]
                     except: pass
            if t: unique_tags.add(t)
                
        all_tags = list(unique_tags)
        matches = [t for t in all_tags if query.lower() in t.lower()]
        
        return dict_to_result(matches[:100], f"Found {len(matches)} tags matching '{query}'")
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
