from mcp_servers.statsmodels_server.tools.core_ops import parse_dataframe, to_serializable, DataInput
from statsmodels.multivariate.pca import PCA
from statsmodels.multivariate.factor import Factor
from statsmodels.multivariate.manova import MANOVA
from statsmodels.multivariate.cancorr import CanCorr
import pandas as pd
from typing import Dict, Any, List, Optional

async def pca(data: DataInput, ncomp: Optional[int] = None, standardize: bool = True) -> Dict[str, Any]:
    """Principal Component Analysis."""
    df = parse_dataframe(data)
    pc = PCA(df, ncomp=ncomp, standardize=standardize)
    return to_serializable({
        "factors": pc.factors, # Components
        "loadings": pc.loadings,
        "explained_variance": pc.eigenvals,
        "rsquare": pc.rsquare.iloc[-1] if isinstance(pc.rsquare, pd.Series) else pc.rsquare
    })

async def factor_analysis(data: DataInput, n_factor: int = 1) -> Dict[str, Any]:
    """Factor Analysis."""
    df = parse_dataframe(data)
    fa = Factor(df, n_factor=n_factor).fit()
    return to_serializable({
        "loadings": fa.loadings,
        "uniqueness": fa.uniqueness,
        "eigenvals": fa.eigenvals
    })

async def manova(endog: DataInput, exog: DataInput) -> Dict[str, Any]:
    """Multivariate ANOVA."""
    y = parse_dataframe(endog)
    x = parse_dataframe(exog)
    mv = MANOVA(y, x)
    return to_serializable({
        "mv_test": mv.mv_test().summary().as_text() # Complex object, return text summary
    })

async def canon_corr(endog: DataInput, exog: DataInput) -> Dict[str, Any]:
    """Canonical Correlation."""
    y = parse_dataframe(endog)
    x = parse_dataframe(exog)
    cc = CanCorr(y, x)
    return to_serializable({
        "cancorr": cc.cancorr,
        "stats": cc.corr_test().summary().as_text()
    })
