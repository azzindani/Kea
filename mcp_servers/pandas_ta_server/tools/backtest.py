
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.pandas_ta_server.tools.core import process_ohlcv, df_to_result
import pandas_ta as ta
import pandas as pd

async def simple_backtest(arguments: dict) -> ToolResult:
    """
    Run a Simple Backtest.
    Args:
        data: OHLCV.
        entry_signal: Logic Query (e.g. "RSI_14 < 30").
        exit_signal: Logic Query (e.g. "RSI_14 > 70").
        # Simplistic: Buy on Entry, Sell on Exit.
    """
    try:
        data = arguments.get("data")
        entry_query = arguments.get("entry_signal")
        exit_query = arguments.get("exit_signal")
        
        df = process_ohlcv(data)
        
        # Calculate All Indicators (to support queries)
        df.ta.strategy("All", verbose=False)
        
        # 1. Identify Entry Points
        entries = df.eval(entry_query) # Series of Booleans
        exits = df.eval(exit_query)    # Series of Booleans
        
        # 2. Simulate Trades (Vectorized-ish loop)
        in_trade = False
        trades = []
        entry_price = 0
        entry_date = None
        
        for i, row in df.iterrows():
            if not in_trade and entries[i]:
                in_trade = True
                entry_price = row['close']
                entry_date = i
            elif in_trade and exits[i]:
                in_trade = False
                exit_price = row['close']
                pnl = (exit_price - entry_price) / entry_price
                trades.append({
                    "entry_date": entry_date,
                    "exit_date": i,
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "pnl": pnl,
                    "pnl_pct": pnl * 100
                })
                
        # 3. Summarize
        if not trades:
             return ToolResult(content=[TextContent(text="No trades generated.")])
             
        df_trades = pd.DataFrame(trades)
        total_return = df_trades['pnl'].sum() * 100
        win_rate = len(df_trades[df_trades['pnl'] > 0]) / len(df_trades) * 100
        
        summary = f"### Backtest Results\n"
        summary += f"**Entries**: {entry_query}\n"
        summary += f"**Exits**: {exit_query}\n"
        summary += f"**Total Trades**: {len(trades)}\n"
        summary += f"**Total Return**: {total_return:.2f}%\n"
        summary += f"**Win Rate**: {win_rate:.2f}%\n"
        
        return ToolResult(content=[TextContent(text=summary)])
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
