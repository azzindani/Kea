
import asyncio
from unittest.mock import MagicMock
import ccxt.async_support as ccxt
from mcp_servers.ccxt_server.server import CcxtServer
from mcp_servers.ccxt_server.tools.exchange_manager import ExchangeManager

# --- Mocking due to Network Block in Agent Environment ---
class MockExchange:
    def __init__(self, config=None):
        self.has = {
            'fetchOHLCV': True, 
            'fetchTicker': True,
            'fetchFundingRate': True, 
            'fetchOpenInterest': True,
            'fetchTrades': True,
            'fetchPositions': True,
            'fetchLiquidations': True,
            'fetchLedger': True,
            'createOrder': True,
            'fetchBorrowRates': True
        }
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
        
    async def fetch_ohlcv(self, symbol, timeframe, since=None, limit=100):
        # Mock History
        # Return different data based on 'since' to simulate pagination loop end
        if since and since > 1672535000000: # Some future mock time
            return []
        return [
            [1672531200000, 100, 105, 95, 102, 1000], 
            [1672534800000, 102, 108, 101, 107, 1200]
        ]

    async def fetch_trades(self, symbol, limit=20):
        return [
            {'timestamp': 1672531200000, 'datetime': '2023-01-01T00:00:00.000Z', 'symbol': symbol, 'side': 'buy', 'price': 65000.0, 'amount': 0.1, 'cost': 6500.0},
            {'timestamp': 1672531201000, 'datetime': '2023-01-01T00:00:01.000Z', 'symbol': symbol, 'side': 'sell', 'price': 65010.0, 'amount': 0.2, 'cost': 13002.0}
        ]
        
    async def fetch_positions(self, symbols=None):
        return [{
            'symbol': 'BTC/USDT', 'timestamp': 1672531200000, 'datetime': '2023-01-01T00:00:00.000Z',
            'side': 'long', 'contracts': 1.0, 'contractSize': 1.0, 'unrealizedPnl': 500.0, 'leverage': 10,
            'entryPrice': 64500.0, 'markPrice': 65000.0, 'collateral': 6500.0
        }]
        
    async def fetch_liquidations(self, symbol, limit=20):
        return [{
            'symbol': symbol, 'price': 64000.0, 'quantity': 0.5, 'timestamp': 1672531200000, 'datetime': '2023-01-01T00:00:00.000Z'
        }]
        
    async def fetch_status(self):
        return {'status': 'ok', 'updated': 1672531200000, 'eta': None, 'url': 'https://binance.com'}
        
    async def fetch_time(self):
        return 1672531200000
    
    async def fetch_funding_rate(self, symbol):
        return {
            'symbol': symbol, 'fundingRate': 0.0001, 'timestamp': 1672531200000, 'nextFundingTime': 1672550000000
        }
        
    async def fetch_open_interest(self, symbol):
        return {
            'symbol': symbol, 'openInterestAmount': 5000.0, 'openInterestValue': 325000000.0, 'timestamp': 1672531200000
        }
        
    async def create_order(self, symbol, type_, side, amount, price=None, params={}):
        return {
            'id': '12345678', 'clientOrderId': 'testOrder', 'timestamp': 1672531200000, 
            'status': 'closed', 'symbol': symbol, 'type': type_, 'side': side, 
            'price': price or 65000.0, 'amount': amount, 'filled': amount, 'remaining': 0.0
        }

    async def fetch_ledger(self, code=None, limit=None):
        return [{
            'id': 'tx123', 'currency': 'USDT', 'amount': 1000.0, 'type': 'deposit', 'status': 'ok', 'timestamp': 1672500000000
        }]
        
    async def fetch_borrow_rates(self):
        return {
            'USDT': {'rate': 0.05, 'timestamp': 1672531200000},
            'BTC': {'rate': 0.01, 'timestamp': 1672531200000}
        }
        
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
         
    except Exception as e:
         print(f"Exception: {e}")
         
    # Test 5: Derivatives (Funding Rate)
    print("\n--- Testing Funding Rate (Binance) ---")
    try:
        handler = server._handlers["get_funding_rate"]
        res = await handler({"exchange": "binance", "symbol": "BTC/USDT"})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:500])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
         print(f"Exception: {e}")

    # Test 6: Historical Download (Pagination) - Mocked
    # Note: Mock fetchOHLCV isn't looping, but logic should handle it.
    print("\n--- Testing History Download (Limited Mock) ---")
    try:
        # We need to mock fetch_ohlcv to return data so download_history works
        # Current mock returns data. The loop will run once or twice depending on timestamps.
        handler = server._handlers["download_history"]
        res = await handler({"exchange": "binance", "symbol": "BTC/USDT", "days": 1})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:500])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
         print(f"Exception: {e}")

    except Exception as e:
         print(f"Exception: {e}")
         
    # Test 7: Private Positions
    print("\n--- Testing Positions (Mocked Auth) ---")
    try:
        handler = server._handlers["get_positions"]
        # Mock doesn't actually check keys
        res = await handler({"exchange": "binance", "api_key": "mock", "secret": "mock"})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:500])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
         print(f"Exception: {e}")

    # Test 8: Global Funding Spread (Aggregator)
    print("\n--- Testing Global Funding Spread (BTC/USDT) ---")
    try:
        handler = server._handlers["get_global_funding_spread"]
        res = await handler({"symbol": "BTC/USDT", "exchanges": ["binance", "kraken"]})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:500])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
         print(f"Exception: {e}")

    except Exception as e:
         print(f"Exception: {e}")

    # Test 9: Trading (Create Order)
    print("\n--- Testing Trading (Create Order Mock) ---")
    try:
        handler = server._handlers["create_order"]
        res = await handler({"exchange": "binance", "symbol": "BTC/USDT", "side": "buy", "type": "limit", "amount": 0.1, "price": 64000, "api_key": "mock", "secret": "mock"})
        if not res.isError:
             print("SUCCESS snippet (Limit Buy):\n", res.content[0].text[:500])
        else:
             print("FAILED:", res.content[0].text)
             
        # Shortcut Buy
        handler_sc = server._handlers["buy_on_binance"]
        res_sc = await handler_sc({"symbol": "BTC/USDT", "type": "market", "amount": 0.01, "price": 0, "api_key": "mock", "secret": "mock"})
        if not res_sc.isError:
            print("SUCCESS Shortcut (Market Buy):\n", res_sc.content[0].text[:500])
            
    except Exception as e:
         print(f"Exception: {e}")

    # Test 10: Ledger
    print("\n--- Testing Ledger ---")
    try:
        handler = server._handlers["get_transaction_history"]
        res = await handler({"exchange": "binance", "api_key": "mock", "secret": "mock"})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:500])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
         print(f"Exception: {e}")

    # await ExchangeManager.close_all() # Mock doesn't need close

if __name__ == "__main__":
    asyncio.run(verify())
