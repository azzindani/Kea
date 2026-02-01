
import os
# Clear MPLBACKEND before importing matplotlib (Kaggle sets invalid value)
os.environ.pop('MPLBACKEND', None)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import yfinance as yf
import uuid
import os

import matplotlib.pyplot as plt
import yfinance as yf
import uuid
import os
import base64
from mcp.server.fastmcp import Image
from shared.logging import get_logger

logger = get_logger(__name__)

async def get_price_chart(ticker: str, period: str = "1y") -> Image:
    """
    Generate a price chart image.
    Args:
        ticker (str): "AAPL"
        period (str): "1y", "6mo", "1mo"
    """
    
    try:
        # Fetch Data
        df = yf.Ticker(ticker).history(period=period)
        if df.empty:
            raise ValueError("No data found")
        
        # Plot
        plt.figure(figsize=(10, 6))
        plt.plot(df.index, df['Close'], label=f"{ticker} Close")
        plt.title(f"{ticker} Price History ({period})")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Save to temp
        img_id = uuid.uuid4().hex[:8]
        filename = f"chart_{ticker}_{img_id}.png"
        path = f"/tmp/{filename}"
        plt.savefig(path)
        plt.close()
        
        # Read for Base64
        with open(path, "rb") as f:
            data = f.read()
            
        return Image(data=data, format="png")
        
    except Exception as e:
        logger.error(f"Chart generation error: {e}")
        raise e

