"""
Analysis MCP Server.

Provides statistical analysis and trend detection tools via MCP.
"""

from __future__ import annotations

import asyncio
import json

from shared.mcp.server_base import MCPServer
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger


logger = get_logger(__name__)


class AnalysisServer(MCPServer):
    """
    MCP Server for data analysis.
    
    Tools:
    - meta_analysis: Compare data across sources
    - trend_detection: Identify patterns and trends
    """
    
    def __init__(self) -> None:
        super().__init__(name="analysis_server", version="1.0.0")
        self._register_tools()
    
    def _register_tools(self) -> None:
        """Register all analysis tools."""
        
        self.register_tool(
            name="meta_analysis",
            description="Perform meta-analysis across multiple data sources. Compare values, identify discrepancies, and compute aggregates.",
            handler=self._handle_meta_analysis,
            parameters={
                "data_points": {
                    "type": "array",
                    "description": "List of data points with source, value, and metadata"
                },
                "analysis_type": {
                    "type": "string",
                    "description": "Type: comparison, consensus, variance, aggregate"
                }
            },
            required=["data_points"]
        )
        
        self.register_tool(
            name="trend_detection",
            description="Detect trends, patterns, and anomalies in time-series or sequential data.",
            handler=self._handle_trend_detection,
            parameters={
                "data": {
                    "type": "array",
                    "description": "Time-series data as [{date, value}] or numeric array"
                },
                "metric_name": {
                    "type": "string",
                    "description": "Name of the metric being analyzed"
                },
                "detect_anomalies": {
                    "type": "boolean",
                    "description": "Whether to detect anomalies (default: true)"
                }
            },
            required=["data"]
        )
    
    async def _handle_meta_analysis(self, arguments: dict) -> ToolResult:
        """Handle meta_analysis tool call."""
        logger.info("Executing meta-analysis")
        
        data_points = arguments.get("data_points", [])
        analysis_type = arguments.get("analysis_type", "comparison")
        
        if not data_points:
            return ToolResult(
                content=[TextContent(text="Error: data_points is required")],
                isError=True
            )
        
        try:
            import statistics
            
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
            
            if not values:
                return ToolResult(
                    content=[TextContent(text="Error: No numeric values found in data_points")],
                    isError=True
                )
            
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
            
            return ToolResult(content=[TextContent(text=output)])
            
        except Exception as e:
            logger.error(f"Meta-analysis error: {e}")
            return ToolResult(
                content=[TextContent(text=f"Error: {str(e)}")],
                isError=True
            )
    
    async def _handle_trend_detection(self, arguments: dict) -> ToolResult:
        """Handle trend_detection tool call."""
        logger.info("Executing trend detection")
        
        data = arguments.get("data", [])
        metric_name = arguments.get("metric_name", "Value")
        detect_anomalies = arguments.get("detect_anomalies", True)
        
        if not data:
            return ToolResult(
                content=[TextContent(text="Error: data is required")],
                isError=True
            )
        
        try:
            import statistics
            
            # Extract values
            values = []
            dates = []
            
            for item in data:
                if isinstance(item, dict):
                    val = item.get("value")
                    if val is not None:
                        values.append(float(val))
                        dates.append(item.get("date", f"T{len(values)}"))
                elif isinstance(item, (int, float)):
                    values.append(float(item))
                    dates.append(f"T{len(values)}")
            
            if len(values) < 2:
                return ToolResult(
                    content=[TextContent(text="Error: Need at least 2 data points")],
                    isError=True
                )
            
            output = f"## Trend Analysis: {metric_name}\n\n"
            output += f"**Data Points:** {len(values)}\n"
            output += f"**Period:** {dates[0]} to {dates[-1]}\n\n"
            
            # Calculate trend
            first_half = values[:len(values)//2]
            second_half = values[len(values)//2:]
            
            mean_first = statistics.mean(first_half)
            mean_second = statistics.mean(second_half)
            
            trend_direction = "📈 Increasing" if mean_second > mean_first else "📉 Decreasing"
            trend_pct = ((mean_second - mean_first) / mean_first * 100) if mean_first != 0 else 0
            
            output += "### Trend Summary\n"
            output += f"- **Direction:** {trend_direction}\n"
            output += f"- **Change:** {trend_pct:+.1f}%\n"
            output += f"- **Start Value:** {values[0]:.2f}\n"
            output += f"- **End Value:** {values[-1]:.2f}\n"
            output += f"- **Overall Change:** {((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0:+.1f}%\n"
            
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
            
            return ToolResult(content=[TextContent(text=output)])
            
        except Exception as e:
            logger.error(f"Trend detection error: {e}")
            return ToolResult(
                content=[TextContent(text=f"Error: {str(e)}")],
                isError=True
            )


async def main() -> None:
    """Run the analysis server."""
    from shared.logging import setup_logging, LogConfig
    
    setup_logging(LogConfig(level="DEBUG", format="console", service_name="analysis_server"))
    
    server = AnalysisServer()
    logger.info(f"Starting {server.name} with {len(server.get_tools())} tools")
    
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
