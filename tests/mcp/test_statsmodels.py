
import pytest
from mcp import ClientSession
from mcp.client.stdio import stdio_client

from tests.mcp.client_utils import get_server_params


@pytest.mark.asyncio
async def test_statsmodels_full_coverage():
    """
    REAL SIMULATION: Verify Statsmodels Server (100% Tool Coverage - 40+ Tools).
    """
    params = get_server_params("statsmodels_server", extra_dependencies=["statsmodels", "scipy", "numpy", "pandas"])

    # Dummy Data - Use more varied data to avoid singularity/convergence issues
    y = [1.2, 2.5, 3.1, 4.8, 5.0]
    # x: Use non-constant columns
    x = [[1.2, 0.5], [2.1, 1.2], [3.3, 2.1], [4.5, 3.5], [5.1, 4.2]]
    x_simple = [1.0, 2.0, 3.0, 4.0, 5.0]

    # Time Data for TSA
    # 20 points for TSA to not error on lag calculation
    y_ts = [i + (i%3)*0.5 for i in range(20)]

    # Discrete Data (Binary)
    y_bin = [0, 1, 0, 1, 0]

    print("\n--- Starting 100% Coverage Simulation: Statsmodels Server ---")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # --- 1. REGRESSION ---
            print("\n[1. Regression]")
            await session.call_tool("ols_model", arguments={"y": y, "x": x})
            await session.call_tool("wls_model", arguments={"y": y, "x": x, "weights": [1]*5})
            await session.call_tool("gls_model", arguments={"y": y, "x": x})
            await session.call_tool("glsar_model", arguments={"y": y, "x": x, "rho": 1})
            await session.call_tool("quant_reg", arguments={"y": y, "x": x, "q": 0.5})
            await session.call_tool("recursive_ls", arguments={"y": y, "x": x})
            await session.call_tool("bulk_ols", arguments={"y": y, "x": x})

            # --- 2. TSA ---
            print("\n[2. TSA]")
            await session.call_tool("adfuller_test", arguments={"x": y_ts})
            await session.call_tool("kpss_test", arguments={"x": y_ts})
            await session.call_tool("decompose", arguments={"x": y_ts, "period": 4})
            await session.call_tool("compute_acf", arguments={"x": y_ts, "nlags": 5})
            await session.call_tool("compute_pacf", arguments={"x": y_ts, "nlags": 5})
            # ARIMA needs enough data. 20 pts might be small for defaults, but should try.
            # Warning: ARIMA might fail convergence or data size, use try-except or robust params.
            # Using simple order.
            await session.call_tool("arima_model", arguments={"endog": y_ts, "order": [1, 0, 0]})
            await session.call_tool("sarimax_model", arguments={"endog": y_ts, "order": [1, 0, 0], "seasonal_order": [0, 0, 0, 0]})
            await session.call_tool("exp_smoothing", arguments={"endog": y_ts, "trend": "add"})
            # Granger needs 2d array (n_samples, n_vars)? Or list of series?
            # Doc says "datasets: List[Union[List[float], str]]" in scipy? No, statsmodels: "data: DataInput".
            # Usually expects DataFrame or 2D array where columns are variables.
            xy_ts = [[y_ts[i], y_ts[i]] for i in range(len(y_ts))] # 2 variables
            await session.call_tool("granger_test", arguments={"data": xy_ts, "maxlag": 2})
            await session.call_tool("auto_select_order", arguments={"y": y_ts})

            # --- 3. DISCRETE ---
            print("\n[3. Discrete]")
            await session.call_tool("logit_model", arguments={"y": y_bin, "x": x})
            await session.call_tool("probit_model", arguments={"y": y_bin, "x": x})
            # MNLogit needs nominal > 2? Or works with binary. Binary usually treated as binomial. MNLogit handles it.
            await session.call_tool("mnlogit_model", arguments={"y": y_bin, "x": x})
            await session.call_tool("poisson_model", arguments={"y": [1, 2, 3, 4, 5], "x": x})
            await session.call_tool("neg_binom_model", arguments={"y": [1, 2, 3, 4, 5], "x": x})

            # --- 4. MULTIVAR ---
            print("\n[4. Multivar]")
            # PCA/FA expect 2D and benefit from non-constant columns
            await session.call_tool("pca", arguments={"data": x, "ncomp": 1})
            await session.call_tool("factor_analysis", arguments={"data": x, "n_factor": 1})

            # MANOVA/CanCorr need non-collinear multi-output
            # y_multi columns should not be perfectly correlated
            y_multi = [[1.2, 0.8], [2.1, 1.5], [3.4, 2.2], [4.1, 3.8], [5.5, 4.5]]
            await session.call_tool("manova", arguments={"endog": y_multi, "exog": x})
            await session.call_tool("canon_corr", arguments={"endog": y_multi, "exog": x})

            # --- 5. NONPARAM ---
            print("\n[5. Nonparam]")
            await session.call_tool("kde_univar", arguments={"data": y})
            # Fix kde_multivar: var_type length must match number of columns
            # Using x which has 2 columns
            await session.call_tool("kde_multivar", arguments={"data": x, "var_type": "cc"})
            await session.call_tool("lowess", arguments={"endog": y, "exog": x_simple})

            # --- 6. STAT TOOLS ---
            print("\n[6. Stat Tools]")
            resids = [0.1, -0.1, 0.2, -0.2, 0.0]
            await session.call_tool("jarque_bera_test", arguments={"resids": resids})
            await session.call_tool("omni_normtest_test", arguments={"resids": [0.1]*8 + [-0.1]*8}) # Need >= 8 samples
            await session.call_tool("durbin_watson_test", arguments={"resids": resids})
            await session.call_tool("het_breuschpagan_test", arguments={"resids": resids, "exog": x})
            await session.call_tool("het_goldfeldquandt_test", arguments={"y": y, "x": x})
            await session.call_tool("stats_describe", arguments={"data": y})
            await session.call_tool("z_test", arguments={"x1": y, "value": 0})
            await session.call_tool("prop_confint", arguments={"count": 5, "nobs": 10})

            # --- 7. SUPER ---
            print("\n[7. Super]")
            await session.call_tool("automl_regression", arguments={"y": y, "x": x})
            await session.call_tool("tsa_dashboard", arguments={"y": y_ts, "period": 4})

    print("--- Statsmodels 100% Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
