import statistics
from typing import List, Dict, Any, Union, Optional

def meta_analysis(data_points: List[Dict[str, Any]], analysis_type: str = "comparison") -> str:
    """Perform meta-analysis across multiple data sources."""
    if not data_points: return "Error: data_points is required"

    # Extract values
    values = []
    sources = []
    
    for dp in data_points:
        if isinstance(dp, dict):
            val = dp.get("value")
            if val is not None:
                try:
                    values.append(float(val))
                    sources.append(dp.get("source", "Unknown"))
                except (ValueError, TypeError):
                    pass
    
    if not values: return "Error: No numeric values found in data_points"
    
    output = f"## Meta-Analysis Results\n\n"
    output += f"**Analysis Type:** {analysis_type}\n"
    output += f"**Data Points:** {len(values)}\n\n"
    
    # Calculate statistics
    output += "### Statistics\n"
    output += f"- **Mean:** {statistics.mean(values):.4f}\n"
    output += f"- **Median:** {statistics.median(values):.4f}\n"
    output += f"- **Min:** {min(values):.4f}\n"
    output += f"- **Max:** {max(values):.4f}\n"
    
    if len(values) > 1:
        output += f"- **Std Dev:** {statistics.stdev(values):.4f}\n"
        output += f"- **Variance:** {statistics.variance(values):.4f}\n"
    
    # Discrepancy analysis
    if analysis_type in ["comparison", "variance"]:
        output += "\n### Source Comparison\n"
        output += "| Source | Value | Deviation from Mean |\n"
        output += "|:-------|------:|--------------------:|\n"
        
        mean_val = statistics.mean(values)
        for i, (src, val) in enumerate(zip(sources, values)):
            dev = val - mean_val
            dev_pct = (dev / mean_val * 100) if mean_val != 0 else 0
            output += f"| {src} | {val:.2f} | {dev_pct:+.1f}% |\n"
    
    # Consensus value
    if analysis_type == "consensus":
        output += f"\n### Consensus Value\n"
        output += f"**Recommended value:** {statistics.median(values):.4f} (median)\n"
        output += f"**Confidence range:** {min(values):.4f} - {max(values):.4f}\n"
    
    return output

def trend_detection(data: List[Union[Dict, float, int]], metric_name: str = "Value", detect_anomalies: bool = True) -> str:
    """Detect trends, patterns, and anomalies in time-series."""
    if not data: return "Error: data is required"

    # Extract values
    values = []
    dates = []
    
    for item in data:
        if isinstance(item, dict):
            val = item.get("value")
            if val is not None:
                try:
                    values.append(float(val))
                    dates.append(item.get("date", f"T{len(values)}"))
                except: pass
        elif isinstance(item, (int, float)):
            values.append(float(item))
            dates.append(f"T{len(values)}")
    
    if len(values) < 2: return "Error: Need at least 2 data points"
    
    output = f"## Trend Analysis: {metric_name}\n\n"
    output += f"**Data Points:** {len(values)}\n"
    output += f"**Period:** {dates[0]} to {dates[-1]}\n\n"
    
    # Calculate trend
    first_half = values[:len(values)//2]
    second_half = values[len(values)//2:]
    
    if not first_half or not second_half: # Should be covered by len<2 but safe check
        return "Insufficient data for trend split."

    mean_first = statistics.mean(first_half)
    mean_second = statistics.mean(second_half)
    
    trend_direction = "📈 Increasing" if mean_second > mean_first else "📉 Decreasing"
    
    change_pct = ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0
    
    output += "### Trend Summary\n"
    output += f"- **Direction:** {trend_direction}\n"
    output += f"- **Start Value:** {values[0]:.2f}\n"
    output += f"- **End Value:** {values[-1]:.2f}\n"
    output += f"- **Overall Change:** {change_pct:+.1f}%\n"
    
    # Anomaly detection
    if detect_anomalies and len(values) >= 4:
        mean = statistics.mean(values)
        stdev = statistics.stdev(values)
        
        anomalies = []
        for i, (date, val) in enumerate(zip(dates, values)):
            z_score = (val - mean) / stdev if stdev > 0 else 0
            if abs(z_score) > 2:  # 2 standard deviations
                anomalies.append({
                    "date": date,
                    "value": val,
                    "z_score": z_score
                })
        
        if anomalies:
            output += "\n### Anomalies Detected\n"
            output += "| Date | Value | Z-Score |\n"
            output += "|:-----|------:|--------:|\n"
            for a in anomalies[:10]:
                output += f"| {a['date']} | {a['value']:.2f} | {a['z_score']:.2f} |\n"
        else:
            output += "\n*No significant anomalies detected.*\n"
    
    return output
