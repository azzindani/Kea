
import matplotlib.pyplot as plt
import yfinance as yf
import uuid
import os
from shared.mcp.protocol import ToolResult, TextContent, ImageContent
from shared.logging import get_logger

logger = get_logger(__name__)

async def get_price_chart(arguments: dict) -> ToolResult:
    """
    Generate a price chart image.
    Args:
        ticker (str): "AAPL"
        period (str): "1y", "6mo", "1mo"
    """
    ticker = arguments.get("ticker")
    period = arguments.get("period", "1y")
    
    try:
        # Fetch Data
        df = yf.Ticker(ticker).history(period=period)
        if df.empty: return ToolResult(isError=True, content=[TextContent(text="No data found")])
        
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
        
        # Read for Base64 (Standard Image Content)
        # However, MCP ImageContent expects base64 string data
        import base64
        with open(path, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode("utf-8")
            
        return ToolResult(content=[
            TextContent(text=f"Chart generated for {ticker}."),
            ImageContent(
                data=b64_data,
                mimeType="image/png"
            )
        ])
        
    except Exception as e:
        logger.error(f"Chart generation error: {e}")
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
