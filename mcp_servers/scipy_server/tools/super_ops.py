from mcp_servers.scipy_server.tools import stats_ops, signal_ops
from mcp_servers.scipy_server.tools.core_ops import parse_data, to_serializable
from scipy import stats
import numpy as np
from typing import Dict, Any, List

async def analyze_distribution(data: List[float]) -> Dict[str, Any]:
    """
    Super Tool: Fit data against top 5 distributions and rank by SSE (Sum Squared Error).
    Distributions: norm, expon, gamma, lognorm, weibull_min.
    """
    arr = parse_data(data)
    
    # Distributions to test
    dists = [stats.norm, stats.expon, stats.gamma, stats.lognorm, stats.weibull_min]
    names = ["norm", "expon", "gamma", "lognorm", "weibull_min"]
    
    results = []
    
    # Histogram for simple SSE check
    y, x = np.histogram(arr, bins=10, density=True)
    x = (x + np.roll(x, -1))[:-1] / 2.0
    
    for dist, name in zip(dists, names):
        # Fit
        params = dist.fit(arr)
        
        # Calculate pdf
        pdf = dist.pdf(x, *params)
        
        # SSE
        sse = np.sum(np.power(y - pdf, 2.0))
        
        results.append({
            "distribution": name,
            "sse": float(sse),
            "params": params
        })
        
    # Sort by SSE
    results.sort(key=lambda k: k['sse'])
    
    return to_serializable({
        "best_fit": results[0],
        "ranking": results
    })

async def signal_dashboard(data: List[float]) -> Dict[str, Any]:
    """
    Super Tool: Perform comprehensive signal analysis (Stats, Peaks, FFT) in one go.
    """
    arr = parse_data(data)
    
    # 1. Descriptive
    desc = await stats_ops.describe_data(arr)
    
    # 2. Peaks
    peaks = await signal_ops.find_peaks(arr)
    
    # 3. FFT (Top 5 Frequencies)
    fft_res = np.abs(np.fft.fft(arr))
    freqs = np.fft.fftfreq(len(arr))
    
    # Sort by magnitude (ignore DC component roughly)
    idx = np.argsort(fft_res)[::-1]
    top_freqs = [{"freq": float(freqs[i]), "mag": float(fft_res[i])} for i in idx[1:6]]
    
    return {
        "stats": desc,
        "peaks_count": len(peaks['peaks']),
        "top_frequencies": top_freqs
    }

async def compare_samples(sample1: List[float], sample2: List[float]) -> Dict[str, Any]:
    """
    Super Tool: Run multiple comparison tests between two samples.
    """
    # T-test
    ttest = await stats_ops.ttest_ind(sample1, sample2)
    # Mann-Whitney
    u_test = await stats_ops.mannwhitneyu(sample1, sample2)
    # KS Test
    ks = await stats_ops.ks_test(sample1) # compares to norm? Wait kstest 2 samp
    
    # KS 2 samp
    arr1 = parse_data(sample1)
    arr2 = parse_data(sample2)
    ks_2 = stats.ks_2samp(arr1, arr2)
    
    return {
        "ttest": ttest,
        "mannwhitney": u_test,
        "ks_2samp": {"statistic": ks_2.statistic, "pvalue": ks_2.pvalue}
    }
