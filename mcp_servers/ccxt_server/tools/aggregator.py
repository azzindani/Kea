
import ccxt.async_support as ccxt
import asyncio
import pandas as pd
import ccxt.async_support as ccxt
import asyncio
import pandas as pd
from shared.logging import get_logger
from mcp_servers.ccxt_server.tools.exchange_manager import get_exchange_instance

logger = get_logger(__name__)

# Default "Top Tier" exchanges for aggregation
TOP_EXCHANGES = ['binance', 'kraken', 'coinbase', 'okx', 'bybit', 'kucoin', 'gateio', 'bitstamp']

async def fetch_price_safe(exchange_id, symbol):
    try:
        ex = await get_exchange_instance(exchange_id)
        ticker = await ex.fetch_ticker(symbol)
        return {
            "exchange": exchange_id,
            "last": ticker['last'],
            "bid": ticker['bid'],
            "ask": ticker['ask'],
            "volume": ticker.get('quoteVolume', 0)
        }
    except Exception as e:
        return {"exchange": exchange_id, "error": str(e)}


# --- AGGREGATOR ---

async def get_global_price(symbol: str = "BTC/USDT", exchanges: list[str] = None) -> str:
    """
    Get Global Price Aggregation for a symbol (e.g. BTC/USDT).
    Fetches from multiple exchanges in parallel.
    """
    if exchanges is None:
        exchanges = TOP_EXCHANGES
    
    # Run parallel
    tasks = [fetch_price_safe(ex_id, symbol) for ex_id in exchanges]
    results = await asyncio.gather(*tasks)
    
    # Filter valid
    valid_data = [r for r in results if "error" not in r and r['last'] is not None]
    errors = [r for r in results if "error" in r]
    
    if not valid_data:
        return f"Failed to fetch {symbol} from any exchange. Errors: {errors}"
        
    df = pd.DataFrame(valid_data)
    
    # limit volume to reasonable number
    if 'volume' in df.columns:
        df['volume'] = df['volume'].fillna(0).astype(float)
    
    # Stats
    mean_price = df['last'].mean()
    min_price = df['last'].min()
    max_price = df['last'].max()
    spread_pct = ((max_price - min_price) / min_price) * 100
    
    summary = f"""### Global Price: {symbol}
**Mean Price**: {mean_price:.4f}
**Spread Range**: {spread_pct:.2f}% (Diff between lowest and highest exchange)
**Sources**: {len(valid_data)} / {len(exchanges)}

{df[['exchange', 'last', 'bid', 'ask', 'volume']].sort_values('last').to_markdown(index=False)}
"""
    return summary



async def get_arbitrage_spread(symbol: str = "BTC/USDT", exchanges: list[str] = None) -> str:
    """
    Scan for Arbitrage Opportunities (Simple Spatial).
    Compare Buy Low (Min Ask) vs Sell High (Max Bid).
    """
    if exchanges is None: exchanges = TOP_EXCHANGES
    
    tasks = [fetch_price_safe(ex_id, symbol) for ex_id in exchanges]
    results = await asyncio.gather(*tasks)
    
    valid = [r for r in results if "error" not in r and r['bid'] and r['ask']]
    
    if len(valid) < 2:
        return "Need at least 2 exchanges with valid data."
        
    df = pd.DataFrame(valid)
    
    # Best Ask (Lowest Price to Buy)
    best_buy = df.loc[df['ask'].idxmin()]
    # Best Bid (Highest Price to Sell)
    best_sell = df.loc[df['bid'].idxmax()]
    
    profit_pct = ((best_sell['bid'] - best_buy['ask']) / best_buy['ask']) * 100
    is_profitable = profit_pct > 0
    
    output = f"""### Arbitrage Scan: {symbol}

**Result**: {"✅ PROFIT OPPORTUNITY" if is_profitable else "❌ No Arbitrage"}
**Potential Profit**: {profit_pct:.3f}%

**Buy At**: {best_buy['exchange']} @ {best_buy['ask']}
**Sell At**: {best_sell['exchange']} @ {best_sell['bid']}

#### Details
{df[['exchange', 'bid', 'ask', 'last']].sort_values('ask').to_markdown(index=False)}
"""
    return output



async def get_global_funding_spread(symbol: str = "BTC/USDT", exchanges: list[str] = None) -> str:
    """
    Compare Funding Rates across exchanges.
    """
    # symbol "BTC/USDT:USDT" usually
    if exchanges is None: exchanges = ['binance', 'bybit', 'okx', 'gateio', 'bitget']
    
    async def fetch_funding(ex_id):
        try:
            ex = await get_exchange_instance(ex_id)
            if hasattr(ex, 'fetchFundingRate'):
                # Note: Unified symbol matching is tricky for funding, usually needs :USDT suffix for some.
                # Just try.
                rate = await ex.fetch_funding_rate(symbol)
                return {
                    "exchange": ex_id,
                    "fundingRate": rate['fundingRate'],
                    "nextFundingTime": rate.get('nextFundingTime')
                }
            return {"exchange": ex_id, "error": "Not Supported"}
        except Exception as e:
            return {"exchange": ex_id, "error": str(e)}
            
    tasks = [fetch_funding(ex_id) for ex_id in exchanges]
    results = await asyncio.gather(*tasks)
    
    valid = [r for r in results if "error" not in r]
    
    if not valid:
         return "No funding data found."
         
    df = pd.DataFrame(valid)
    df = df.sort_values('fundingRate', ascending=False)
    
    return f"### Global Funding Rates: {symbol}\n\n{df.to_markdown()}"

