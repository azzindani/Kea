
import ccxt.async_support as ccxt
import asyncio
from typing import Optional
from shared.logging.structured import get_logger

logger = get_logger(__name__)

class ExchangeManager:
    _instances = {}
    _lock: Optional[asyncio.Lock] = None
    
    @classmethod
    async def get_exchange(cls, exchange_id: str):
        """
        Get or create an exchange instance.
        """
        if cls._lock is None:
            cls._lock = asyncio.Lock()
            
        exchange_id = exchange_id.lower()
        
        async with cls._lock:
            if exchange_id in cls._instances:
                return cls._instances[exchange_id]
                
            if not hasattr(ccxt, exchange_id):
                raise ValueError(f"Exchange '{exchange_id}' not supported by CCXT.")
                
            try:
                exchange_class = getattr(ccxt, exchange_id)
                exchange = exchange_class({
                    'enableRateLimit': True,
                    # 'verbose': True
                })
            except Exception as e:
                logger.error(f"Failed to create exchange instance {exchange_id}: {e}")
                raise

            try:
                # Load markets immediately? Or lazy load?
                # Better to load once.
                logger.info(f"Loading markets for {exchange_id}...")
                await exchange.load_markets()
                
                cls._instances[exchange_id] = exchange
                return exchange
            except Exception as e:
                logger.error(f"Failed to init {exchange_id}: {e}")
                # Ensure we close if validation fails
                try:
                    await exchange.close()
                    # Allow run loop to cleanup underlying connections
                    await asyncio.sleep(0.01)
                except Exception as close_error:
                    logger.error(f"Failed to close exchange {exchange_id}: {close_error}")
                raise

    @classmethod
    async def close_all(cls):
        for _, exchange in cls._instances.items():
            await exchange.close()
        cls._instances.clear()

# Global accessor
async def get_exchange_instance(exchange_id: str):
    return await ExchangeManager.get_exchange(exchange_id)
