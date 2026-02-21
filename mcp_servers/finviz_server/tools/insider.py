
from finvizfinance.insider import Insider

from shared.logging.main import get_logger

logger = get_logger(__name__)

# Map friendly name to library option
# option: latest, top week, top owner
OPTS = {
    "latest_buys": "latest buys",
    "latest_sales": "latest sales",
    "top_week_buys": "top week buys",
    "top_week_sales": "top week sales",
    "top_owner_buys": "top owner buys",
    "top_owner_sales": "top owner sales"
}


async def get_insider_market(subset: str = "latest_buys") -> str:
    """
    Get market-wide insider transactions.
    subset: "latest_buys", "top_week_sales", etc.
    """
    # subset = arguments.get("subset", "latest_buys")
    real_opt = OPTS.get(subset, "latest buys")
    
    try:
        ins = Insider(option=real_opt)
        df = ins.get_insider()
        
        # Limit columns if possible, but default is usually okay.
        return f"### Insider: {subset}\n\n{df.head(30).to_markdown()}"
    except Exception as e:
        logger.error(f"Insider error {subset}: {e}")
        return f"Error: {str(e)}"

