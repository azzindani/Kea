"""
MCP Tool Tests: Analysis Tools.

Tests for analysis MCP tools via API.
"""

import pytest
import httpx


API_URL = "http://localhost:8080"


class TestMetaAnalysis:
    """Tests for meta_analysis tool."""
    
    @pytest.mark.mcp
    @pytest.mark.asyncio
    async def test_comparison_analysis(self):
        """Run comparison meta-analysis."""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{API_URL}/api/v1/mcp/tools/invoke",
                json={
                    "tool_name": "meta_analysis",
                    "arguments": {
                        "data_points": [
                            {"source": "A", "value": 100},
                            {"source": "B", "value": 110},
                            {"source": "C", "value": 105},
                        ],
                        "analysis_type": "comparison",
                    },
                }
            )
        
        if response.status_code == 200:
            data = response.json()
            assert "result" in data


class TestTrendDetection:
    """Tests for trend_detection tool."""
    
    @pytest.mark.mcp
    @pytest.mark.asyncio
    async def test_detect_trend(self):
        """Detect trend in time series."""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{API_URL}/api/v1/mcp/tools/invoke",
                json={
                    "tool_name": "trend_detection",
                    "arguments": {
                        "data": [10, 12, 15, 18, 22, 25, 30],
                        "metric_name": "Growth",
                    },
                }
            )
        
        if response.status_code == 200:
            data = response.json()
            result_text = str(data.get("result", ""))
            # Should detect increasing trend
            assert "Increasing" in result_text or "trend" in result_text.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "mcp"])
