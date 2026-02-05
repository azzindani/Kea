from mcp_servers.statsmodels_server.tools.core_ops import parse_dataframe, parse_series, to_serializable, DataInput, VectorInput
import statsmodels.nonparametric.api as nparam
from statsmodels.nonparametric.kde import KDEUnivariate
from statsmodels.nonparametric.kernel_density import KDEMultivariate
import numpy as np
from typing import Dict, Any, List, Optional

async def kde_univar(data: VectorInput, kernel: str = 'gau', fft: bool = True) -> Dict[str, Any]:
    """Univariate Kernel Density Estimation."""
    kde = KDEUnivariate(parse_series(data))
    kde.fit(kernel=kernel, fft=fft)
    return to_serializable({
        "support": kde.support,
        "density": kde.density,
        "cdf": kde.cdf
    })

# KDEMultivariate is heavy, handle with care
async def kde_multivar(data: DataInput, var_type: str) -> Dict[str, Any]:
    """
    Multivariate Kernel Density Estimation.
    var_type: string of 'c' (continuous), 'u' (unordered discrete), 'o' (ordered). e.g. 'cc'
    """
    df = parse_dataframe(data)
    kde = KDEMultivariate(data=df, var_type=var_type)
    # Return pdf at data points?
    pdf = kde.pdf(df)
    return to_serializable({"pdf": pdf.tolist(), "bw": kde.bw.tolist()})

async def lowess(endog: VectorInput, exog: VectorInput, frac: float = 2.0/3.0, it: int = 3) -> List[List[float]]:
    """Locally Weighted Scatterplot Smoothing."""
    y = parse_series(endog)
    x = parse_series(exog)
    res = nparam.lowess(y, x, frac=frac, it=it)
    return to_serializable(res.tolist())
