
from finvizfinance.screener.overview import Overview
from shared.logging.main import get_logger

logger = get_logger(__name__)

# PRESET DICTIONARIES
# These map friendly names to Finviz Screener filter dicts.
PRESETS = {
    # Basic
    "value_stocks": {"P/E": "Under 15", "P/B": "Under 1", "Debt/Equity": "Under 0.5"},
    "growth_stocks": {"EPS growth this year": "Over 20%", "EPS growth next year": "Over 20%", "Sales growth past 5 years": "Over 20%"},
    "high_yield_dividend": {"Dividend Yield": "Over 5%", "Payout Ratio": "Under 50%"},
    
    # Technical / Momentum
    "oversold_bounce": {"RSI (14)": "Oversold (30)", "Performance": "Today Up"},
    "overbought_pullback": {"RSI (14)": "Overbought (70)", "Performance": "Today Down"},
    "new_highs_volume": {"Performance": "Month +20%", "Average Volume": "Over 500K", "Current Volume": "Over 1M"},
    "golden_cross": {"20-Day Simple Moving Average": "Price above SMA20", "50-Day Simple Moving Average": "SMA50 above SMA200", "200-Day Simple Moving Average": "SMA200 below SMA50"}, # Approx
    "death_cross": {"50-Day Simple Moving Average": "SMA50 below SMA200"},
    
    # Volatility / breakouts
    "high_volatility": {"Volatility": "Month - Over 5%"},
    "short_squeeze_candidate": {"Float Short": "Over 20%", "Performance": "Today Up"},
    "low_float_runners": {"Float": "Under 20M", "Relative Volume": "Over 2", "Performance": "Today Up"},
    
    # Fundamental
    "undervalued_growth": {"PEG": "Under 1", "EPS growth next year": "Over 15%"},
    "market_leaders": {"Index": "S&P 500", "Performance": "Year +30%"},
    "penny_stock_volume": {"Price": "Under $5", "Average Volume": "Over 1M"},
    "debt_free_cash_rich": {"Debt/Equity": "Under 0.1", "Quick Ratio": "Over 2"},
    
    # Insider
    "insider_buy_signals": {"InsiderTransactions": "Very Positive (>20%)"}, # Note: Key might be specific
    "institution_buying": {"InstitutionalOwnership": "Over 70%", "InstitutionalTransactions": "Positive (>0.1%)"}
}


async def get_strategy_screen(limit: int = 100000, strategy: str = None) -> str:
    """
    Run a complex strategy filter preset.
    strategy: "value_stocks", "growth_stocks", etc.
    """
    # strategy = arguments.get("strategy")
    # limit = arguments.get("limit", 30)
    
    if strategy not in PRESETS:
        return "Invalid strategy"
        
    filters = PRESETS[strategy]
    
    try:
        foverview = Overview()
        foverview.set_filter(filters_dict=filters)
        
        df = foverview.screener_view()
        if df is None or df.empty:
            return "No results found for strategy."
            
        cols = ["Ticker", "Company", "Sector", "Price", "Change", "Volume"]
        cols = [c for c in cols if c in df.columns]
        
        return f"### Strategy: {strategy}\nFilters: {filters}\n\n{df[cols].head(limit).to_markdown(index=False)}"
        
    except Exception as e:
        logger.error(f"Strategy error {strategy}: {e}")
        return f"Error: {str(e)}"

