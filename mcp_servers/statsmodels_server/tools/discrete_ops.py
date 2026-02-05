from mcp_servers.statsmodels_server.tools.core_ops import parse_dataframe, to_serializable, format_summary, DataInput
import statsmodels.api as sm
from typing import Dict, Any, List, Optional

async def _fit_discrete(model_class, y, x, **kwargs) -> Dict[str, Any]:
    y_arr = parse_dataframe(y)
    x_arr = sm.add_constant(parse_dataframe(x))
    model = model_class(y_arr, x_arr, **kwargs)
    try:
        res = model.fit(disp=0)
    except:
        res = model.fit() # MnLogit sometimes diverse args
        
    return to_serializable({
        "params": res.params,
        "pvalues": res.pvalues,
        "aic": res.aic,
        "prsquared": getattr(res, "prsquared", None), # Pseudo R2
        "margeff": res.get_margeff().summary().as_text() if hasattr(res, 'get_margeff') else None,
        "summary": format_summary(res)
    })

async def logit_model(y: DataInput, x: DataInput) -> Dict[str, Any]:
    """Logistic Regression."""
    return await _fit_discrete(sm.Logit, y, x)

async def probit_model(y: DataInput, x: DataInput) -> Dict[str, Any]:
    """Probit Regression."""
    return await _fit_discrete(sm.Probit, y, x)

async def mnlogit_model(y: DataInput, x: DataInput) -> Dict[str, Any]:
    """Multinomial Logit."""
    return await _fit_discrete(sm.MNLogit, y, x)

async def poisson_model(y: DataInput, x: DataInput) -> Dict[str, Any]:
    """Poisson Regression."""
    return await _fit_discrete(sm.Poisson, y, x)

async def neg_binom_model(y: DataInput, x: DataInput, alpha: float = 1.0) -> Dict[str, Any]:
    """Negative Binomial Regression."""
    # NegBinom needs alpha usually or estimates it?
    # statsmodels estimate alpha? Default NegBinomial
    return await _fit_discrete(sm.NegativeBinomial, y, x)
