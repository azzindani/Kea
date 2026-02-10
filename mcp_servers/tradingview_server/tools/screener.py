import json
import requests
import structlog

logger = structlog.get_logger(__name__)

# Standard columns that act as "Bulk Data" for any ticker
DEFAULT_COLUMNS = [
    "name", "description", "logoid", 
    "close", "change", "change_abs", "Val.Traded", "volume", 
    "market_cap_basic", "price_earnings_ttm", "earnings_per_share_basic_ttm",
    "number_of_employees", "sector", "RSI", "MACD.macd", "MACD.signal"
]

class TvScreener:
    """
    Custom engine to query scanner.tradingview.com directly.
    Allows fetching 100+ rows with arbitrary columns (Bulk Data).
    """
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Content-Type": "application/json"
        }

    def fetch(self, market="america", query=None, columns=None, range_limit=100) -> list:
        url = f"https://scanner.tradingview.com/{market}/scan"
        
        cols = columns if columns else DEFAULT_COLUMNS
        
        # Default query if none provided (Get everything, sorted by Market Cap)
        sort_data = query.get("sort", {"field": "market_cap_basic", "order": "desc"}) if query else {"field": "market_cap_basic", "order": "desc"}
        
        # Ensure we use 'field' and 'order' for the API
        if "sortBy" in sort_data:
            sort_data["field"] = sort_data.pop("sortBy")
        if "sortOrder" in sort_data:
            sort_data["order"] = sort_data.pop("sortOrder")

        payload = {
            "columns": cols,
            "filter": query.get("filter", []) if query else [],
            "options": {"lang": "en"},
            "range": [0, min(range_limit, 1000)], # Cap at 1000 for safety
            "sort": sort_data,
            "symbols": {"query": {"types": []}, "tickers": []}
        }

        # If strict symbol list is provided (Bulk Data Mode)
        if query and "symbol_list" in query:
            payload["symbols"] = {"tickers": query["symbol_list"], "query": {"types": []}}
            payload.pop("filter", None) # Filters might conflict with explicit tickers
            payload.pop("sort", None)
        elif query and "symbols" in query:
            payload["symbols"] = query["symbols"]

        try:
            # Use json= parameter to automatically set Content-Type and handle serialization
            resp = requests.post(url, headers=self.headers, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            # Formatter
            results = []
            for item in data["data"]:
                row = {"ticker": item["s"]}
                # Map raw values to column names
                for i, col in enumerate(cols):
                    val = item["d"][i]
                    row[col] = val
                results.append(row)
            return results
        except Exception as e:
            logger.error(f"Screener fetch error: {e}")
            return [{"error": str(e)}]

# --- TOOL HANDLERS ---


async def scan_market(market: str = "america", limit: int = 100000, preset: str = "market_cap") -> str:
    """
    General Screener Tool.
    Args:
        market (str): "america", "indonesia", "crypto", "forex".
        limit (int): Max results (default 50).
        preset (str): "top_gainers", "top_losers", "most_active", "oversold", "overbought".
    """
    screener = TvScreener()
    query = {"sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"}}
    
    # Presets Logic
    if preset == "top_gainers":
        query["sort"] = {"field": "change", "order": "desc"}
    elif preset == "top_losers":
        query["sort"] = {"field": "change", "order": "asc"}
    elif preset == "most_active":
        query["sort"] = {"field": "volume", "order": "desc"}
    elif preset == "oversold":
        query["filter"] = [{"left": "RSI", "operation": "less", "right": 30}]
        query["sort"] = {"field": "RSI", "order": "asc"}
    elif preset == "overbought":
        query["filter"] = [{"left": "RSI", "operation": "greater", "right": 70}]
        query["sort"] = {"field": "RSI", "order": "desc"}
        
    data = screener.fetch(market=market, query=query, range_limit=limit)
    return json.dumps(data, indent=2)




async def get_bulk_data(tickers: list[str], columns: list[str] = None, market: str = "america") -> str:
    """
    MULTI-TALENT: Fetch specific data columns for a list of tickers.
    Args:
        tickers (list[str]): ["NASDAQ:AAPL", "IDX:BBCA"]
        columns (list[str] | None): ["close", "RSI", "volume", "sector"]
        market (str): "america", "indonesia" (Required if not fully qualified)
    """
    if columns is None:
        columns = ["close", "change", "volume", "RSI", "MACD.macd"]
        
    screener = TvScreener()
    # "symbol_list" triggers the bulk mode in fetch()
    query = {"symbol_list": tickers}
    
    data = screener.fetch(market=market, query=query, columns=columns, range_limit=len(tickers))
    return json.dumps(data, indent=2)


