import os
import uuid
import base64
import matplotlib
import matplotlib.pyplot as plt
import yfinance as yf
from mcp.server.fastmcp import Image
from shared.logging.main import get_logger

# Clear MPLBACKEND before importing matplotlib
os.environ.pop('MPLBACKEND', None)
matplotlib.use("Agg")

logger = get_logger(__name__)

async def get_price_chart(ticker: str, period: str = "1y", **kwargs) -> Image:
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
        temp_dir = os.environ.get("TEMP", os.environ.get("TMP", "/tmp"))
        path = os.path.join(temp_dir, filename)
        plt.savefig(path)
        plt.close()
        
        # Read for Base64
        with open(path, "rb") as f:
            data = f.read()
            
        return Image(data=data, format="png")
        
    except Exception as e:
        logger.error(f"Chart generation error: {e}")
        raise e

