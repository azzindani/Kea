from mcp_servers.statsmodels_server.tools.core_ops import parse_dataframe, parse_series, to_serializable, DataInput, VectorInput
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, kpss, grangercausalitytests, coint, acf, pacf, arma_order_select_ic
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import pandas as pd
from typing import Dict, Any, List, Optional, Union

async def adfuller_test(x: VectorInput, autolag: str = 'AIC') -> Dict[str, Any]:
    """Augmented Dickey-Fuller unit root test."""
    res = adfuller(parse_series(x), autolag=autolag)
    return to_serializable({
        "adf_stat": res[0],
        "pvalue": res[1],
        "usedlag": res[2],
        "nobs": res[3],
        "critical_values": res[4]
    })

async def kpss_test(x: VectorInput, regression: str = 'c') -> Dict[str, Any]:
    """KPSS test for stationarity."""
    res = kpss(parse_series(x), regression=regression)
    return to_serializable({
        "kpss_stat": res[0],
        "pvalue": res[1],
        "lags": res[2],
        "critical_values": res[3]
    })

async def decompose(x: VectorInput, model: str = 'additive', period: Optional[int] = None) -> Dict[str, Any]:
    """Seasonal decomposition."""
    res = seasonal_decompose(parse_series(x), model=model, period=period)
    return to_serializable({
        "trend": res.trend,
        "seasonal": res.seasonal,
        "resid": res.resid
    })

async def compute_acf(x: VectorInput, nlags: int = 40) -> List[float]:
    """Autocorrelation function."""
    return to_serializable(acf(parse_series(x), nlags=nlags))

async def compute_pacf(x: VectorInput, nlags: int = 40) -> List[float]:
    """Partial Autocorrelation function."""
    return to_serializable(pacf(parse_series(x), nlags=nlags))

async def arima_model(endog: VectorInput, order: List[int] = [1, 0, 0]) -> Dict[str, Any]:
    """Fit ARIMA model."""
    res = ARIMA(parse_series(endog), order=tuple(order)).fit()
    return to_serializable({
        "params": res.params,
        "aic": res.aic,
        "bic": res.bic,
        "summary": res.summary().as_text()
    })

async def sarimax_model(endog: VectorInput, order: List[int], seasonal_order: List[int], exog: Optional[DataInput] = None) -> Dict[str, Any]:
    """Fit SARIMAX model."""
    ex = parse_dataframe(exog) if exog else None
    res = SARIMAX(parse_series(endog), exog=ex, order=tuple(order), seasonal_order=tuple(seasonal_order)).fit(disp=False)
    return to_serializable({
        "params": res.params,
        "aic": res.aic,
        "summary": res.summary().as_text()
    })

async def exp_smoothing(endog: VectorInput, trend: str = None, seasonal: str = None, seasonal_periods: int = None) -> Dict[str, Any]:
    """Holt-Winters Exponential Smoothing."""
    model = ExponentialSmoothing(parse_series(endog), trend=trend, seasonal=seasonal, seasonal_periods=seasonal_periods)
    res = model.fit()
    return to_serializable({
        "params": res.params,
        "aic": res.aic,
        "forecast": res.forecast(10)
    })

async def granger_test(data: DataInput, maxlag: int = 4) -> Dict[str, Any]:
    """Granger Causality Test. Data must be 2 columns."""
    df = parse_dataframe(data)
    # statsmodels expects 2d array
    res = grangercausalitytests(df, maxlag=maxlag, verbose=False)
    # output is complex, simplify
    parsed = {}
    for lag, v in res.items():
        parsed[f"lag_{lag}"] = {
            "ssr_ftest_p": v[0]['ssr_ftest'][1],
            "ssr_chi2test_p": v[0]['ssr_chi2test'][1]
        }
    return to_serializable(parsed)

async def auto_select_order(y: VectorInput, max_ar: int = 4, max_ma: int = 2) -> Dict[str, Any]:
    """Compute AIC/BIC for various ARMA orders."""
    res = arma_order_select_ic(parse_series(y), max_ar=max_ar, max_ma=max_ma, ic=['aic', 'bic'])
    return to_serializable({
        "aic_min_order": res.aic_min_order,
        "bic_min_order": res.bic_min_order
    })
