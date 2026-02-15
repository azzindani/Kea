import pandas as pd
import structlog
# Note: statsmodels is not installed in the basic list. 
# We must ensure it's in dependencies or use it carefully.
# The previous user requirements implied `statsmodels` was a "Primary Server" category (Analysis).
# I will assume it's available or add it.

from typing import Dict, Any, List, Optional
import warnings

warnings.filterwarnings("ignore")
logger = structlog.get_logger()

# Helper
def _load_ts(file_path: str, value_col: str, date_col: str = None) -> pd.Series:
    df = pd.read_csv(file_path)
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.set_index(date_col)
        df = df.sort_index()
    # If no date col, assume ordered index
    return df[value_col].dropna()

def model_ols_regression(file_path: str, formula: str) -> Dict[str, Any]:
    """RUNS OLS Linear Regression (Formula). [DATA]"""
    try:
        import statsmodels.formula.api as smf
        df = pd.read_csv(file_path)
        model = smf.ols(formula=formula, data=df).fit()
        return {
            "summary": str(model.summary2()),
            "rsquared": model.rsquared,
            "params": model.params.to_dict(),
            "pvalues": model.pvalues.to_dict()
        }
    except ImportError:
        return {"error": "statsmodels not installed"}
    except Exception as e:
        return {"error": str(e)}

def model_ar(file_path: str, value_col: str, date_col: str = None, lags: int = 1) -> Dict[str, Any]:
    """RUNS AutoRegressive Model. [DATA]"""
    try:
        from statsmodels.tsa.ar_model import AutoReg
        series = _load_ts(file_path, value_col, date_col)
        model = AutoReg(series, lags=lags).fit()
        return {
            "params": model.params.to_dict(),
            "aic": model.aic,
            "bic": model.bic
        }
    except Exception as e:
        return {"error": str(e)}

def model_arima(file_path: str, value_col: str, order: List[int], date_col: str = None) -> Dict[str, Any]:
    """RUNS ARIMA Model. [DATA]"""
    try:
        from statsmodels.tsa.arima.model import ARIMA
        series = _load_ts(file_path, value_col, date_col)
        model = ARIMA(series, order=tuple(order)).fit()
        return {
            "params": model.params.to_dict(),
            "aic": model.aic,
            "summary": str(model.summary())
        }
    except Exception as e:
        return {"error": str(e)}

def model_exponential_smoothing(file_path: str, value_col: str, seasonal: str = None, seasonal_periods: int = 12, date_col: str = None) -> Dict[str, Any]:
    """RUNS Exponential Smoothing (Holt-Winters). [DATA]"""
    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        series = _load_ts(file_path, value_col, date_col)
        # Statsmodels requires frequency often, or use simple index
        if series.index.freq is None and date_col:
             # Try infer
             pass
        
        model = ExponentialSmoothing(series, seasonal=seasonal, seasonal_periods=seasonal_periods).fit()
        return {
            "params": model.params,
            "sse": model.sse,
            "optimized": True
        }
    except Exception as e:
        return {"error": str(e)}

def test_adfuller(file_path: str, value_col: str) -> Dict[str, Any]:
    """PERFORMS Augmented Dickey-Fuller Test. [DATA]"""
    try:
        from statsmodels.tsa.stattools import adfuller
        series = _load_ts(file_path, value_col)
        result = adfuller(series)
        return {
            "adf_statistic": result[0],
            "p_value": result[1],
            "used_lag": result[2],
            "n_obs": result[3],
            "critical_values": result[4],
            "stationary": result[1] < 0.05
        }
    except Exception as e:
        return {"error": str(e)}
