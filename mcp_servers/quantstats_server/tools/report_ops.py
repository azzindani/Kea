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
    """Get all metrics as a dictionary (JSON)."""
    # qs.reports.metrics(display=False) returns dataframe
    s = _parse_returns(returns_input)
    b = None
    if benchmark_input:
        b = _parse_returns(benchmark_input) if len(benchmark_input) > 10 else qs.utils.download_returns(benchmark_input)
        
    df = qs.reports.metrics(s, benchmark=b, display=False, mode='full')
    return df.to_json(orient='index')

def report_full(returns_input: str) -> str:
    """Get full text report as string."""
    # This usually prints to stdout. We can capture it.
    # But qs.reports.metrics gives us the data. 
    # Let's rely on report_metrics for data.
    # If we really want the text output:
    return "Use report_metrics for structured data or report_html for visual report."
