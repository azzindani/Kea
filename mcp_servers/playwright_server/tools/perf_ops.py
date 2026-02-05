from mcp_servers.playwright_server.session_manager import BrowserSession
from typing import Dict, Any, Optional

async def get_performance_metrics() -> Dict[str, float]:
    """
    Get page loading metrics via window.performance.timing
    Returns timings in milliseconds.
    """
    page = await BrowserSession.get_page()
    
    # Raw JSON from evaluate might need parsing
    metrics = await page.evaluate("""() => {
        const timing = window.performance.timing;
        if (!timing) return {};
        
        return {
            navigationStart: timing.navigationStart,
            loadEventEnd: timing.loadEventEnd,
            responseStart: timing.responseStart,
            domInteractive: timing.domInteractive,
            
            # Calculated metrics
            ttfb: timing.responseStart - timing.navigationStart,
            domLoad: timing.domComplete - timing.domInteractive,
            fullLoad: timing.loadEventEnd - timing.navigationStart
        };
    }""")
    return metrics

async def start_tracing(path: str = "trace.zip", screenshots: bool = True, snapshots: bool = True) -> str:
    """
    Start recording a performance trace (Playwright Tracing).
    This records screenshots, DOM, and network.
    Warning: This accumulates data in memory until stopped.
    """
    context = await BrowserSession.get_context()
    await context.tracing.start(screenshots=screenshots, snapshots=snapshots, sources=True)
    return f"Tracing started. Stop tracing to save to {path}"

async def stop_tracing(path: str = "trace.zip") -> str:
    """Stop tracing and save the file."""
    context = await BrowserSession.get_context()
    await context.tracing.stop(path=path)
    return f"Tracing stoped and saved to {path}"
