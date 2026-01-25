
import asyncio
from unittest.mock import MagicMock
import ccxt.async_support as ccxt
from mcp_servers.ccxt_server.server import CcxtServer
from mcp_servers.ccxt_server.tools.exchange_manager import ExchangeManager

# --- Mocking due to Network Block in Agent Environment ---
class MockExchange:
    def __init__(self, config=None):
        self.has = {'fetchOHLCV': True, 'fetchTicker': True}
        self.symbols = ['BTC/USDT', 'ETH/USDT']
        
    async def load_markets(self):
        pass
        
    async def close(self):
        pass
        
    async def fetch_ticker(self, symbol):
        # Return valid structure
        return {
            'symbol': symbol,
            'last': 65000.0,
            'bid': 64990.0,
            'ask': 65010.0,
            'high': 66000.0,
            'low': 64000.0,
            'baseVolume': 100.0,
            'quoteVolume': 6500000.0,
            'percentage': 2.5,
            'datetime': '2023-01-01T00:00:00.000Z'
        }

    async def fetch_order_book(self, symbol, limit=10):
        # Return mock book
        return {
            'bids': [[64990, 1.0], [64980, 2.0]],
            'asks': [[65010, 1.0], [65020, 2.0]]
        }

    async def fetch_trades(self, symbol, limit=20):
        return [
            {'timestamp': 1672531200000, 'datetime': '2023-01-01T00:00:00.000Z', 'symbol': symbol, 'side': 'buy', 'price': 65000.0, 'amount': 0.1, 'cost': 6500.0},
            {'timestamp': 1672531201000, 'datetime': '2023-01-01T00:00:01.000Z', 'symbol': symbol, 'side': 'sell', 'price': 65010.0, 'amount': 0.2, 'cost': 13002.0}
        ]
        
    async def fetch_status(self):
        return {'status': 'ok', 'updated': 1672531200000, 'eta': None, 'url': 'https://binance.com'}
        
    async def fetch_time(self):
        return 1672531200000

# Monkeypatch ExchangeManager to return Mock
original_get = ExchangeManager.get_exchange


async def mock_get_exchange(exchange_id):
    ex = MockExchange()
    
    if exchange_id == "binance": 
        async def ft_binance(symbol):
            return {
                'symbol': symbol, 'last': 65000.0, 'bid': 64990.0, 'ask': 65010.0, 
                'high': 66000.0, 'low': 64000.0, 'baseVolume': 100.0, 'quoteVolume': 6500000.0, 
                'percentage': 2.5, 'datetime': '2023-01-01T00:00:00.000Z'
            }
        ex.fetch_ticker = ft_binance
        
    elif exchange_id == "kraken":
        async def ft_kraken(symbol):
            return {
                'symbol': symbol, 'last': 65100.0, 'bid': 65090.0, 'ask': 65110.0, 
                'high': 66100.0, 'low': 64100.0, 'baseVolume': 100.0, 'quoteVolume': 6510000.0, 
                'percentage': 2.5, 'datetime': '2023-01-01T00:00:00.000Z'
            }
        ex.fetch_ticker = ft_kraken
        
    elif exchange_id == "coinbase":
        async def ft_coinbase(symbol):
            return {
                'symbol': symbol, 'last': 64950.0, 'bid': 64940.0, 'ask': 64960.0, 
                'high': 65950.0, 'low': 63950.0, 'baseVolume': 100.0, 'quoteVolume': 6495000.0, 
                'percentage': 2.5, 'datetime': '2023-01-01T00:00:00.000Z'
            }
        ex.fetch_ticker = ft_coinbase
        
    return ex

ExchangeManager.get_exchange = mock_get_exchange

async def verify():
    print("--- Verifying CCXT Server (Simulated Network) ---")
    server = CcxtServer()
    tools = server.get_tools()
    print(f"Total Tools Registered: {len(tools)}")
    
    # Test 1: Unified Ticker (Binance)
    print("\n--- Testing Unified Ticker (Binance: BTC/USDT) ---")
    try:
        handler = server._handlers["get_ticker"]
        res = await handler({"exchange": "binance", "symbol": "BTC/USDT"})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:300])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Exception: {e}")

    # Test 2: Global Price Aggregator
    print("\n--- Testing Global Price Aggregator (BTC/USDT) ---")
    try:
        handler = server._handlers["get_global_price"]
        res = await handler({"symbol": "BTC/USDT", "exchanges": ["binance", "kraken", "coinbase"]})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:500])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
         print(f"Exception: {e}")

    # Test 3: Arbitrage Spread
    print("\n--- Testing Arbitrage Scan (BTC/USDT) ---")
    try:
        handler = server._handlers["get_arbitrage_spread"]
        res = await handler({"symbol": "BTC/USDT", "exchanges": ["binance", "kraken"]})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:500])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
         print(f"Exception: {e}")
         
    # Test 4: Shortcut (Binance Trades)
    print("\n--- Testing Shortcut: get_binance_trades (BTC/USDT) ---")
    try:
        handler = server._handlers["get_binance_trades"]
        res = await handler({"symbol": "BTC/USDT"})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:500])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
         print(f"Exception: {e}")
         
    # await ExchangeManager.close_all() # Mock doesn't need close

if __name__ == "__main__":
    asyncio.run(verify())
