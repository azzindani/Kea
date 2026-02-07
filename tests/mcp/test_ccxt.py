import pytest
import asyncio
from unittest.mock import MagicMock
import ccxt.async_support as ccxt
from mcp_servers.ccxt_server.server import CcxtServer
from mcp_servers.ccxt_server.tools.exchange_manager import ExchangeManager

# --- Mocking due to Network Block in Agent Environment ---
class MockExchange:
    def __init__(self, config=None):
        self.has = {
            'fetchOHLCV': True, 'fetchTicker': True, 'fetchFundingRate': True, 
            'fetchOpenInterest': True, 'fetchTrades': True, 'fetchPositions': True,
            'fetchLiquidations': True, 'fetchLedger': True, 'createOrder': True,
            'fetchBorrowRates': True
        }
        self.symbols = ['BTC/USDT', 'ETH/USDT']
        
    async def load_markets(self): pass
    async def close(self): pass
        
    async def fetch_ticker(self, symbol):
        return {
            'symbol': symbol, 'last': 65000.0, 'bid': 64990.0, 'ask': 65010.0,
            'high': 66000.0, 'low': 64000.0, 'baseVolume': 100.0, 'quoteVolume': 6500000.0,
            'percentage': 2.5, 'datetime': '2023-01-01T00:00:00.000Z'
        }

    async def fetch_order_book(self, symbol, limit=10):
        return {'bids': [[64990, 1.0]], 'asks': [[65010, 1.0]]}
        
    async def fetch_ohlcv(self, symbol, timeframe, since=None, limit=100):
        if since and since > 1672535000000: return []
        return [[1672531200000, 100, 105, 95, 102, 1000]]

    async def fetch_trades(self, symbol, limit=20):
        return [{'timestamp': 1672531200000, 'symbol': symbol, 'price': 65000.0}]
        
    async def fetch_funding_rate(self, symbol):
        return {'symbol': symbol, 'fundingRate': 0.0001, 'timestamp': 1672531200000}

# Monkeypatch ExchangeManager to return Mock
async def mock_get_exchange(exchange_id):
    ex = MockExchange()
    # Mock different prices for arbitrage test
    if exchange_id == "binance": 
        ex.fetch_ticker = lambda s: {'symbol': s, 'last': 65000.0, 'bid': 64990.0, 'ask': 65010.0}
    elif exchange_id == "kraken":
        ex.fetch_ticker = lambda s: {'symbol': s, 'last': 65100.0, 'bid': 65090.0, 'ask': 65110.0}
    return ex

@pytest.fixture
def mock_ccxt(monkeypatch):
    monkeypatch.setattr(ExchangeManager, "get_exchange", mock_get_exchange)

@pytest.mark.asyncio
async def test_ccxt_ticker(mock_ccxt):
    server = CcxtServer()
    handler = server._handlers["get_ticker"]
    res = await handler({"exchange": "binance", "symbol": "BTC/USDT"})
    assert not res.isError
    assert "65000.0" in res.content[0].text

@pytest.mark.asyncio
async def test_ccxt_arbitrage(mock_ccxt):
    server = CcxtServer()
    handler = server._handlers["get_arbitrage_spread"]
    res = await handler({"symbol": "BTC/USDT", "exchanges": ["binance", "kraken"]})
    assert not res.isError
    # validation logic: spread should be detected
    assert "spread" in res.content[0].text.lower()

@pytest.mark.asyncio
async def test_ccxt_history(mock_ccxt):
    server = CcxtServer()
    handler = server._handlers["download_history"]
    res = await handler({"exchange": "binance", "symbol": "BTC/USDT", "days": 1})
    assert not res.isError
    assert "Downloaded" in res.content[0].text
