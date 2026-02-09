from mcp_servers.statsmodels_server.tools.core_ops import parse_dataframe, parse_series, to_serializable, DataInput, VectorInput
import statsmodels.nonparametric.api as nparam
from statsmodels.nonparametric.kde import KDEUnivariate
from statsmodels.nonparametric.kernel_density import KDEMultivariate
from typing import Dict, Any, List

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
    
    # Validation: var_type must match number of columns
    if len(var_type) != df.shape[1]:
        logger.warning("kde_multivar_var_type_mismatch", var_type=var_type, n_cols=df.shape[1])
        # Try to adapt var_type if it's a single character repeated? No, better to be explicit.
        raise ValueError(f"var_type length ({len(var_type)}) must match number of columns in data ({df.shape[1]}). "
                         "Example: 'cc' for two continuous variables.")

    kde = KDEMultivariate(data=df, var_type=var_type)
    # Return pdf at data points
    pdf = kde.pdf(df)
    return to_serializable({"pdf": pdf.tolist(), "bw": kde.bw.tolist()})

async def lowess(endog: VectorInput, exog: VectorInput, frac: float = 2.0/3.0, it: int = 3) -> List[List[float]]:
    """Locally Weighted Scatterplot Smoothing."""
    y = parse_series(endog)
    x = parse_series(exog)
    res = nparam.lowess(y, x, frac=frac, it=it)
    return to_serializable(res.tolist())
