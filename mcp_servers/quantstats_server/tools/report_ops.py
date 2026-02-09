from mcp_servers.quantstats_server.tools.core_ops import _parse_returns
import quantstats as qs
import os
import tempfile
import base64
import warnings

# Suppress warnings that might clutter logs
warnings.filterwarnings('ignore')

def report_html(returns_input: str, benchmark_input: str = None, title: str = "Strategy Report") -> str:
    """Generate Full HTML Tearsheet and return path or content."""
    s = _parse_returns(returns_input)
    b = None
    if benchmark_input:
        b = _parse_returns(benchmark_input) if len(benchmark_input) > 10 else qs.utils.download_returns(benchmark_input)
    
    # Generate to temp file
    fd, path = tempfile.mkstemp(suffix=".html")
    os.close(fd)
    
    qs.reports.html(s, benchmark=b, title=title, output=path, download_filename=path)
    # Read back? Or just return path? 
    # Returning path is safer if large. But user might want content.
    # Let's return path.
    return str(path)

def report_metrics(returns_input: str, benchmark_input: str = None) -> str:
    """Metric report table."""
    s = _parse_returns(returns_input)
    # Ensure DatetimeIndex
    if not isinstance(s.index, pd.DatetimeIndex):
        s.index = pd.to_datetime(s.index)
        
    b = None
    if benchmark_input:
        b = _parse_returns(benchmark_input) if len(benchmark_input) > 20 else qs.utils.download_returns(benchmark_input)
        if b is not None and not isinstance(b.index, pd.DatetimeIndex):
            b.index = pd.to_datetime(b.index)
            
    df = qs.reports.metrics(s, benchmark=b, display=False, mode='full')
    return df.to_json(orient='split')

def report_full(returns_input: str) -> str:
    """Full performance report."""
    s = _parse_returns(returns_input)
    # Ensure DatetimeIndex
    if not isinstance(s.index, pd.DatetimeIndex):
        s.index = pd.to_datetime(s.index)
    return qs.reports.metrics(s, display=False).to_json(orient='split')
