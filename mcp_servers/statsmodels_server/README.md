# 🔌 Statsmodels Server

The `statsmodels_server` is an MCP server providing tools for **Statsmodels Server** functionality.
It is designed to be used within the Kea ecosystem.

## 🧰 Tools

| Tool | Description | Arguments |
|:-----|:------------|:----------|
| `ols_model` | Execute ols model operation | `y: DataInput, x: DataInput, formula: Optional[str] = None` |
| `wls_model` | Execute wls model operation | `y: DataInput, x: DataInput, weights: DataInput` |
| `gls_model` | Execute gls model operation | `y: DataInput, x: DataInput, sigma: Optional[DataInput] = None` |
| `glsar_model` | Execute glsar model operation | `y: DataInput, x: DataInput, rho: int = 1` |
| `quant_reg` | Execute quant reg operation | `y: DataInput, x: DataInput, q: float = 0.5` |
| `recursive_ls` | Execute recursive ls operation | `y: DataInput, x: DataInput` |
| `bulk_ols` | Execute bulk ols operation | `y: DataInput, x: DataInput` |
| `adfuller_test` | Execute adfuller test operation | `x: VectorInput, autolag: str = 'AIC'` |
| `kpss_test` | Execute kpss test operation | `x: VectorInput, regression: str = 'c'` |
| `decompose` | Execute decompose operation | `x: VectorInput, model: str = 'additive', period: Optional[int] = None` |
| `compute_acf` | Execute compute acf operation | `x: VectorInput, nlags: int = 40` |
| `compute_pacf` | Execute compute pacf operation | `x: VectorInput, nlags: int = 40` |
| `arima_model` | Execute arima model operation | `endog: VectorInput, order: List[int] = [1, 0, 0]` |
| `sarimax_model` | Execute sarimax model operation | `endog: VectorInput, order: List[int], seasonal_order: List[int], exog: Optional[DataInput] = None` |
| `exp_smoothing` | Execute exp smoothing operation | `endog: VectorInput, trend: str = None, seasonal: str = None, seasonal_periods: int = None` |
| `granger_test` | Execute granger test operation | `data: DataInput, maxlag: int = 4` |
| `auto_select_order` | Execute auto select order operation | `y: VectorInput, max_ar: int = 4, max_ma: int = 2` |
| `logit_model` | Execute logit model operation | `y: DataInput, x: DataInput` |
| `probit_model` | Execute probit model operation | `y: DataInput, x: DataInput` |
| `mnlogit_model` | Execute mnlogit model operation | `y: DataInput, x: DataInput` |
| `poisson_model` | Execute poisson model operation | `y: DataInput, x: DataInput` |
| `neg_binom_model` | Execute neg binom model operation | `y: DataInput, x: DataInput, alpha: float = 1.0` |
| `pca` | Execute pca operation | `data: DataInput, ncomp: Optional[int] = None, standardize: bool = True` |
| `factor_analysis` | Execute factor analysis operation | `data: DataInput, n_factor: int = 1` |
| `manova` | Execute manova operation | `endog: DataInput, exog: DataInput` |
| `canon_corr` | Execute canon corr operation | `endog: DataInput, exog: DataInput` |
| `kde_univar` | Execute kde univar operation | `data: VectorInput, kernel: str = 'gau', fft: bool = True` |
| `kde_multivar` | Execute kde multivar operation | `data: DataInput, var_type: str` |
| `lowess` | Execute lowess operation | `endog: VectorInput, exog: VectorInput, frac: float = 2.0/3.0, it: int = 3` |
| `jarque_bera_test` | Execute jarque bera test operation | `resids: VectorInput` |
| `omni_normtest_test` | Execute omni normtest test operation | `resids: VectorInput` |
| `durbin_watson_test` | Execute durbin watson test operation | `resids: VectorInput` |
| `het_breuschpagan_test` | Execute het breuschpagan test operation | `resids: VectorInput, exog: DataInput` |
| `het_goldfeldquandt_test` | Execute het goldfeldquandt test operation | `y: VectorInput, x: DataInput` |
| `stats_describe` | Execute stats describe operation | `data: DataInput` |
| `z_test` | Execute z test operation | `x1: VectorInput, x2: Optional[VectorInput] = None, value: float = 0` |
| `prop_confint` | Execute prop confint operation | `count: int, nobs: int, alpha: float = 0.05` |
| `automl_regression` | Execute automl regression operation | `y: DataInput, x: DataInput` |
| `tsa_dashboard` | Execute tsa dashboard operation | `y: DataInput, period: int = 12` |

## 📦 Dependencies

The following packages are required:
- `statsmodels`
- `scipy`
- `numpy`
- `pandas`

## 🚀 Usage

This server is automatically discovered by the **MCP Host**. To run it manually:

```bash
uv run python -m mcp_servers.statsmodels_server.server
```
