
import json
import requests
import asyncio
from shared.mcp.protocol import ToolResult, TextContent, ImageContent
from shared.logging import get_logger

logger = get_logger(__name__)

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
            "Content-Type": "application/x-www-form-urlencoded"
        }

    def fetch(self, market="america", query=None, columns=None, range_limit=100) -> list:
        url = f"https://scanner.tradingview.com/{market}/scan"
        
        cols = columns if columns else DEFAULT_COLUMNS
        
        # Default query if none provided (Get everything, sorted by Market Cap)
        payload = {
            "columns": cols,
            "filter": query.get("filter", []) if query else [],
            "options": {"lang": "en"},
            "range": [0, range_limit],
            "sort": query.get("sort", {"sortBy": "market_cap_basic", "sortOrder": "desc"}) if query else {"sortBy": "market_cap_basic", "sortOrder": "desc"},
            "symbols": query.get("symbols", {"query": {"types": []}}) if query else {"query": {"types": []}}
        }

        # If strict symbol list is provided (Bulk Data Mode)
        if query and "symbol_list" in query:
            payload["symbols"] = {"tickers": query["symbol_list"]}
            payload.pop("filter", None) # Filters might conflict with explicit tickers
            payload.pop("sort", None)

        try:
            resp = requests.post(url, headers=self.headers, data=json.dumps(payload), timeout=10)
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

async def scan_market(arguments: dict) -> ToolResult:
    """
    General Screener Tool.
    Args:
        market (str): "america", "indonesia", "crypto", "forex".
        limit (int): Max results (default 50).
        preset (str): "top_gainers", "top_losers", "most_active", "oversold", "overbought".
    """
    market = arguments.get("market", "america")
    limit = int(arguments.get("limit", 50))
    preset = arguments.get("preset", "market_cap")
    
    screener = TvScreener()
    query = {"sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"}}
    
    # Presets Logic
    if preset == "top_gainers":
        query["sort"] = {"sortBy": "change", "sortOrder": "desc"}
    elif preset == "top_losers":
        query["sort"] = {"sortBy": "change", "sortOrder": "asc"}
    elif preset == "most_active":
        query["sort"] = {"sortBy": "volume", "sortOrder": "desc"}
    elif preset == "oversold":
        query["filter"] = [{"left": "RSI", "operation": "less", "right": 30}]
        query["sort"] = {"sortBy": "RSI", "sortOrder": "asc"}
    elif preset == "overbought":
        query["filter"] = [{"left": "RSI", "operation": "greater", "right": 70}]
        query["sort"] = {"sortBy": "RSI", "sortOrder": "desc"}
        
    data = screener.fetch(market=market, query=query, range_limit=limit)
    return ToolResult(content=[TextContent(text=json.dumps(data, indent=2))])


async def get_bulk_data(arguments: dict) -> ToolResult:
    """
    MULTI-TALENT: Fetch specific data columns for a list of tickers.
    Args:
        tickers (list[str]): ["NASDAQ:AAPL", "IDX:BBCA"]
        columns (list[str]): ["close", "RSI", "volume", "sector"]
        market (str): "america", "indonesia" (Required if not fully qualified)
    """
    tickers = arguments.get("tickers")
    columns = arguments.get("columns", ["close", "change", "volume", "RSI", "MACD.macd"])
    market = arguments.get("market", "america")
    
    screener = TvScreener()
    # "symbol_list" triggers the bulk mode in fetch()
    query = {"symbol_list": tickers}
    
    data = screener.fetch(market=market, query=query, columns=columns, range_limit=len(tickers))
    return ToolResult(content=[TextContent(text=json.dumps(data, indent=2))])

