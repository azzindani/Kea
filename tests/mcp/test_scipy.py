import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_scipy_full_coverage():
    """
    REAL SIMULATION: Verify Scipy Server (100% Tool Coverage - 70+ Tools).
    """
    params = get_server_params("scipy_server", extra_dependencies=["scipy", "numpy", "pandas"])
    
    # Dummy Data - Increased size to avoid SmallSampleWarning (normaltest needs >= 8)
    data = [1.0, 2.0, 3.0, 4.0, 5.0, 1.2, 2.2, 3.2, 4.2, 5.2]
    data2 = [1.1, 2.1, 3.1, 4.1, 5.1, 1.3, 2.3, 3.3, 4.3, 5.3]
    matrix = [[1.0, 2.0], [3.0, 4.0]]
    matrix2 = [[5.0, 6.0], [7.0, 8.0]]
    points = [[0, 0], [0, 1], [1, 0], [1, 1]]
    
    print(f"\n--- Starting 100% Coverage Simulation: Scipy Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # --- 1. STATISTICS ---
            print("\n[1. Statistics]")
            await session.call_tool("describe_data", arguments={"data": data})
            await session.call_tool("get_percentiles", arguments={"data": data})
            await session.call_tool("get_zscore", arguments={"data": data})
            await session.call_tool("get_iqr", arguments={"data": data})
            await session.call_tool("get_entropy", arguments={"data": data})
            await session.call_tool("get_mode", arguments={"data": [1, 1, 2, 3]})
            
            # Tests
            await session.call_tool("test_normality", arguments={"data": data})
            await session.call_tool("ttest_ind", arguments={"data1": data, "data2": data2})
            await session.call_tool("ttest_rel", arguments={"data1": data, "data2": data2})
            await session.call_tool("mannwhitneyu", arguments={"data1": data, "data2": data2})
            await session.call_tool("wilcoxon", arguments={"data1": data, "data2": data2})
            await session.call_tool("kruskal", arguments={"datasets": [data, data2]})
            await session.call_tool("anova_oneway", arguments={"datasets": [data, data2]})
            await session.call_tool("ks_test", arguments={"data": data})
            
            # Correlations
            await session.call_tool("pearson_corr", arguments={"data1": data, "data2": data2})
            await session.call_tool("spearman_corr", arguments={"data1": data, "data2": data2})
            await session.call_tool("kendall_corr", arguments={"data1": data, "data2": data2})
            
            # Fitting
            await session.call_tool("fit_norm", arguments={"data": data})
            await session.call_tool("fit_expon", arguments={"data": data})
            await session.call_tool("fit_gamma", arguments={"data": data})
            await session.call_tool("fit_beta", arguments={"data": data})
            await session.call_tool("fit_lognorm", arguments={"data": data})
            await session.call_tool("fit_weibull", arguments={"data": data})
            
            # --- 2. OPTIMIZATION ---
            print("\n[2. Optimization]")
            func_quad = "x**2 + 5"
            await session.call_tool("minimize_scalar", arguments={"func_str": func_quad})
            # minimize_bfgs requires x0 list
            await session.call_tool("minimize_bfgs", arguments={"func_str": "x[0]**2 + x[1]**2", "x0": [1.0, 1.0]})
            await session.call_tool("minimize_nelder", arguments={"func_str": "x[0]**2 + x[1]**2", "x0": [1.0, 1.0]})
            await session.call_tool("find_root", arguments={"func_str": "x**2 - 4", "a": 0, "b": 3})
            await session.call_tool("curve_fit", arguments={"func_str": "a*x + b", "x_data": [0, 1, 2], "y_data": [1, 3, 5]})
            await session.call_tool("linear_sum_assignment", arguments={"cost_matrix": [[1, 2], [3, 4]]})
            await session.call_tool("linprog", arguments={"c": [-1, -2], "bounds": [[0, None], [0, None]]})
            
            # Global
            await session.call_tool("basinhopping", arguments={"func_str": "x[0]**2", "x0": [1.0]})
            await session.call_tool("differential_evolution", arguments={"func_str": "x[0]**2", "bounds": [[-5, 5]]})
            await session.call_tool("dual_annealing", arguments={"func_str": "x[0]**2", "bounds": [[-5, 5]]})
            
            # --- 3. INTEGRATION ---
            print("\n[3. Integration]")
            await session.call_tool("integrate_quad", arguments={"func_str": "x**2", "a": 0, "b": 1})
            await session.call_tool("integrate_simpson", arguments={"y_data": [0, 1, 4], "dx": 0.5})
            await session.call_tool("integrate_trapezoid", arguments={"y_data": [0, 1, 4], "dx": 0.5})
            await session.call_tool("solve_ivp", arguments={"func_str": "-0.5*t*y", "t_span": [0, 10], "y0": [4.0]})
            
            # --- 4. SIGNAL ---
            print("\n[4. Signal]")
            sig = [0, 1, 2, 1, 0, 1, 2, 1, 0]
            await session.call_tool("find_peaks", arguments={"data": sig})
            await session.call_tool("fft", arguments={"data": sig})
            await session.call_tool("ifft", arguments={"data_real": sig})
            await session.call_tool("resample", arguments={"data": sig, "num": 10})
            await session.call_tool("medfilt", arguments={"data": sig})
            await session.call_tool("wiener", arguments={"data": sig})
            await session.call_tool("savgol_filter", arguments={"data": sig})
            await session.call_tool("detrend", arguments={"data": [1, 2, 3, 4]})
            
            # --- 5. LINALG ---
            print("\n[5. LinAlg]")
            await session.call_tool("matrix_inv", arguments={"matrix": [[1, 2], [3, 4]]}) # Might fail if singular, but [1,2;3,4] det=-2 ok
            await session.call_tool("matrix_det", arguments={"matrix": matrix})
            await session.call_tool("matrix_norm", arguments={"matrix": matrix})
            await session.call_tool("solve_linear", arguments={"a": matrix, "b": [1, 1]})
            await session.call_tool("svd_decomp", arguments={"matrix": matrix})
            await session.call_tool("eig_decomp", arguments={"matrix": matrix})
            await session.call_tool("lu_factor", arguments={"matrix": matrix})
            # Cholesky requires positive definite
            pd_mat = [[2, 1], [1, 2]]
            await session.call_tool("cholesky", arguments={"matrix": pd_mat})
            
            # --- 6. SPATIAL ---
            print("\n[6. Spatial]")
            await session.call_tool("distance_euclidean", arguments={"u": [0, 0], "v": [1, 1]})
            await session.call_tool("distance_cosine", arguments={"u": [1, 0], "v": [0, 1]})
            await session.call_tool("distance_matrix", arguments={"x": [[0, 0]], "y": [[1, 1]]})
            await session.call_tool("convex_hull", arguments={"points": points})
            
            # --- 7. SUPER ---
            print("\n[7. Super]")
            await session.call_tool("analyze_distribution", arguments={"data": data})
            await session.call_tool("signal_dashboard", arguments={"data": sig})
            await session.call_tool("compare_samples", arguments={"sample1": data, "sample2": data2})
            
            # --- 8. INTERP ---
            print("\n[8. Interp]")
            await session.call_tool("interp_1d", arguments={"x": [0, 1], "y": [0, 1], "x_new": [0.5]})
            await session.call_tool("interp_spline", arguments={"x": [0, 1, 2, 3], "y": [0, 1, 0, 1], "x_new": [0.5, 1.5]})
            
            # --- 9. CLUSTERING ---
            print("\n[9. Clustering]")
            await session.call_tool("kmeans", arguments={"data": points, "k_or_guess": 2})
            await session.call_tool("whitening", arguments={"data": points})
            Z = [[0, 1, 0.1, 2], [2, 3, 0.5, 3]] # Fake Z ? Use helper tool?
            # actually we can make linkage of small data
            # linkage helper
            # await session.call_tool("linkage_matrix", arguments={...}) # wait this tool is in server? yes
            Z_real = await session.call_tool("linkage_matrix", arguments={"data": points})
            # Need to parse tool result (it returns text string of list)?
            # ClientSession automatically unwraps content to text.
            # But the next tool expects List[List]. Server decodes JSON.
            # So we can't chain directly unless we parse.
            # For simplicity, we just call using dummy Z for coverage if possible, or skip dependency.
            # Or use result of previous call if we can parse.
            # We'll use a dummy valid Z for fcluster:
            # Z: [idx1, idx2, dist, count]
            Z_dummy = [[0, 1, 0.1, 2], [2, 3, 0.2, 3], [4, 5, 0.3, 4]]
            await session.call_tool("fcluster", arguments={"Z": Z_dummy, "t": 0.5})
            
            # --- 10. ND-IMAGE ---
            print("\n[10. ND-Image]")
            img = [[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 0.0]]
            await session.call_tool("img_gaussian", arguments={"data": img, "sigma": 1.0})
            await session.call_tool("img_sobel", arguments={"data": img})
            await session.call_tool("img_laplace", arguments={"data": img})
            await session.call_tool("img_median", arguments={"data": img})
            await session.call_tool("center_of_mass", arguments={"data": img})
            
            # --- 11. SPECIAL ---
            print("\n[11. Special]")
            await session.call_tool("gamma_func", arguments={"z": [1, 2, 3]})
            await session.call_tool("beta_func", arguments={"a": [1, 2], "b": [2, 1]})
            await session.call_tool("erf_func", arguments={"z": [0, 1]})
            await session.call_tool("bessel_j0", arguments={"z": [0, 1]})

    print("--- Scipy 100% Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
