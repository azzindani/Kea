"""
Regulatory Data MCP Server.

Provides tools for government and regulatory data:
- SEC EDGAR - Company filings
- eCFR - Code of Federal Regulations
- Federal Register - New regulations
- Global sources - WTO, IMF, OECD
"""

from __future__ import annotations

from typing import Any
import re

from shared.mcp.server_base import MCPServerBase
from shared.mcp.protocol import Tool, ToolInputSchema, ToolResult, TextContent
from shared.logging import get_logger


logger = get_logger(__name__)


class RegulatoryServer(MCPServerBase):
    """MCP server for regulatory and government data."""
    
    def __init__(self) -> None:
        super().__init__(name="regulatory_server")
    
    def get_tools(self) -> list[Tool]:
        """Return available tools."""
        return [
            Tool(
                name="edgar_search",
                description="Search SEC EDGAR for company filings (10-K, 10-Q, 8-K, etc.)",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "company": {"type": "string", "description": "Company name or CIK"},
                        "filing_type": {"type": "string", "description": "Type: 10-K, 10-Q, 8-K, DEF 14A, etc."},
                        "date_from": {"type": "string", "description": "Start date YYYY-MM-DD"},
                        "date_to": {"type": "string", "description": "End date YYYY-MM-DD"},
                    },
                    required=["company"],
                ),
            ),
            Tool(
                name="edgar_filing_content",
                description="Get content of a specific SEC filing",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "accession_number": {"type": "string", "description": "Filing accession number"},
                        "section": {"type": "string", "description": "Section to extract: all, risk_factors, mda, financials"},
                    },
                    required=["accession_number"],
                ),
            ),
            Tool(
                name="ecfr_search",
                description="Search eCFR (Code of Federal Regulations)",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "query": {"type": "string", "description": "Search query"},
                        "title": {"type": "integer", "description": "CFR Title number (1-50)"},
                    },
                    required=["query"],
                ),
            ),
            Tool(
                name="federal_register_search",
                description="Search Federal Register for new rules and notices",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "query": {"type": "string", "description": "Search query"},
                        "document_type": {"type": "string", "description": "Type: rule, proposed_rule, notice"},
                        "agency": {"type": "string", "description": "Agency name"},
                    },
                    required=["query"],
                ),
            ),
            Tool(
                name="wto_data",
                description="Get WTO trade statistics and agreements",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "indicator": {"type": "string", "description": "Indicator: trade_growth, tariffs, disputes"},
                        "country": {"type": "string", "description": "Country code"},
                        "year": {"type": "integer", "description": "Year"},
                    },
                    required=["indicator"],
                ),
            ),
            Tool(
                name="imf_data",
                description="Get IMF economic data and forecasts",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "indicator": {"type": "string", "description": "Indicator: gdp, inflation, debt"},
                        "country": {"type": "string", "description": "Country code or 'world'"},
                        "year": {"type": "string", "description": "Year or range 2020-2024"},
                    },
                    required=["indicator"],
                ),
            ),
        ]
    
    async def handle_tool_call(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        """Handle tool call."""
        try:
            if name == "edgar_search":
                return await self._handle_edgar_search(arguments)
            elif name == "edgar_filing_content":
                return await self._handle_edgar_content(arguments)
            elif name == "ecfr_search":
                return await self._handle_ecfr(arguments)
            elif name == "federal_register_search":
                return await self._handle_federal_register(arguments)
            elif name == "wto_data":
                return await self._handle_wto(arguments)
            elif name == "imf_data":
                return await self._handle_imf(arguments)
            else:
                return ToolResult(
                    content=[TextContent(text=f"Unknown tool: {name}")],
                    isError=True,
                )
        except Exception as e:
            logger.error(f"Tool {name} failed: {e}")
            return ToolResult(
                content=[TextContent(text=f"Error: {str(e)}")],
                isError=True,
            )
    
    async def _handle_edgar_search(self, args: dict) -> ToolResult:
        """Search SEC EDGAR."""
        import httpx
        
        company = args["company"]
        filing_type = args.get("filing_type", "")
        date_from = args.get("date_from")
        date_to = args.get("date_to")
        
        # SEC EDGAR API
        headers = {"User-Agent": "Research Bot research@example.com"}
        
        async with httpx.AsyncClient(timeout=30, headers=headers) as client:
            # Search for company
            search_url = f"https://efts.sec.gov/LATEST/search-index"
            params = {
                "q": company,
                "dateRange": "custom",
                "forms": filing_type if filing_type else "10-K,10-Q,8-K",
            }
            if date_from:
                params["startdt"] = date_from
            if date_to:
                params["enddt"] = date_to
            
            # Use full-text search API
            search_resp = await client.get(
                "https://efts.sec.gov/LATEST/search-index",
                params={"q": company, "forms": filing_type or "10-K"}
            )
            
            # Alternative: Company search
            company_resp = await client.get(
                f"https://www.sec.gov/cgi-bin/browse-edgar",
                params={
                    "action": "getcompany",
                    "company": company,
                    "type": filing_type,
                    "output": "atom",
                }
            )
        
        result = f"# 📊 SEC EDGAR Search\n\n"
        result += f"**Company**: {company}\n"
        if filing_type:
            result += f"**Filing Type**: {filing_type}\n"
        result += "\n"
        
        # Parse results
        from xml.etree import ElementTree
        try:
            root = ElementTree.fromstring(company_resp.text)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            
            entries = root.findall("atom:entry", ns)
            result += f"**Results**: {len(entries)}\n\n"
            
            for entry in entries[:10]:
                title = entry.find("atom:title", ns)
                link = entry.find("atom:link", ns)
                updated = entry.find("atom:updated", ns)
                
                if title is not None:
                    result += f"### {title.text}\n"
                    if updated is not None:
                        result += f"- **Date**: {updated.text[:10]}\n"
                    if link is not None:
                        result += f"- **Link**: [{link.get('href')}]({link.get('href')})\n"
                    result += "\n"
        except Exception as e:
            result += f"Note: Could not parse EDGAR response. Search at: https://www.sec.gov/cgi-bin/browse-edgar?company={company}\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_edgar_content(self, args: dict) -> ToolResult:
        """Get EDGAR filing content."""
        import httpx
        
        accession = args["accession_number"].replace("-", "")
        section = args.get("section", "all")
        
        headers = {"User-Agent": "Research Bot research@example.com"}
        
        result = f"# 📄 SEC Filing Content\n\n"
        result += f"**Accession**: {accession}\n\n"
        
        # This would require parsing HTML/XML filings
        result += "To access filing content:\n"
        result += f"- EDGAR: https://www.sec.gov/Archives/edgar/data/{accession}/\n"
        result += "- Use document parser tools to extract specific sections\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_ecfr(self, args: dict) -> ToolResult:
        """Search eCFR."""
        import httpx
        
        query = args["query"]
        title = args.get("title")
        
        async with httpx.AsyncClient(timeout=30) as client:
            params = {"query": query, "per_page": 10}
            if title:
                params["title"] = title
            
            response = await client.get(
                "https://www.ecfr.gov/api/search/v1/results",
                params=params
            )
            
            if response.status_code != 200:
                return ToolResult(content=[TextContent(
                    text=f"eCFR search failed. Manual search: https://www.ecfr.gov/search?query={query}"
                )])
            
            data = response.json()
        
        result = f"# 📜 eCFR Search Results\n\n"
        result += f"**Query**: {query}\n\n"
        
        results = data.get("results", [])
        result += f"**Found**: {len(results)}\n\n"
        
        for item in results[:10]:
            title_num = item.get("hierarchy", {}).get("title", "")
            section = item.get("hierarchy", {}).get("section", "")
            heading = item.get("headings", {}).get("section", "No heading")
            
            result += f"### {heading}\n"
            result += f"- **Citation**: {title_num} CFR {section}\n"
            result += f"- **Link**: https://www.ecfr.gov/current/title-{title_num}/section-{section}\n\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_federal_register(self, args: dict) -> ToolResult:
        """Search Federal Register."""
        import httpx
        
        query = args["query"]
        doc_type = args.get("document_type")
        agency = args.get("agency")
        
        params = {
            "conditions[term]": query,
            "per_page": 10,
            "order": "newest",
        }
        if doc_type:
            params["conditions[type][]"] = doc_type
        if agency:
            params["conditions[agencies][]"] = agency
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                "https://www.federalregister.gov/api/v1/documents",
                params=params
            )
            data = response.json()
        
        result = f"# 📰 Federal Register Search\n\n"
        result += f"**Query**: {query}\n\n"
        
        documents = data.get("results", [])
        result += f"**Found**: {data.get('count', len(documents))}\n\n"
        
        for doc in documents[:10]:
            title = doc.get("title", "No title")
            doc_type = doc.get("type", "")
            pub_date = doc.get("publication_date", "")
            agencies = ", ".join(a.get("name", "") for a in doc.get("agencies", [])[:2])
            html_url = doc.get("html_url", "")
            
            result += f"### {title[:80]}...\n" if len(title) > 80 else f"### {title}\n"
            result += f"- **Type**: {doc_type}\n"
            result += f"- **Date**: {pub_date}\n"
            result += f"- **Agency**: {agencies}\n"
            result += f"- **Link**: [{html_url}]({html_url})\n\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_wto(self, args: dict) -> ToolResult:
        """Get WTO data."""
        indicator = args["indicator"]
        country = args.get("country")
        year = args.get("year")
        
        result = f"# 🌍 WTO Data\n\n"
        result += f"**Indicator**: {indicator}\n"
        if country:
            result += f"**Country**: {country}\n"
        result += "\n"
        
        # WTO has complex API, provide links
        result += "## Data Sources\n\n"
        result += "- [Trade Profiles](https://www.wto.org/english/res_e/statis_e/trade_profiles_list_e.htm)\n"
        result += "- [Statistics Database](https://stats.wto.org/)\n"
        result += "- [Documents](https://docs.wto.org/)\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_imf(self, args: dict) -> ToolResult:
        """Get IMF data."""
        import httpx
        
        indicator = args["indicator"]
        country = args.get("country", "world")
        year = args.get("year")
        
        result = f"# 💰 IMF Data\n\n"
        result += f"**Indicator**: {indicator}\n"
        result += f"**Country**: {country}\n\n"
        
        # IMF DataMapper API
        indicator_map = {
            "gdp": "NGDP_RPCH",
            "inflation": "PCPIPCH",
            "debt": "GGXWDG_NGDP",
        }
        
        code = indicator_map.get(indicator.lower(), indicator)
        
        result += "## Data Source\n\n"
        result += f"- [IMF DataMapper](https://www.imf.org/external/datamapper/{code}@WEO)\n"
        result += f"- [World Economic Outlook](https://www.imf.org/en/Publications/WEO)\n"
        
        return ToolResult(content=[TextContent(text=result)])


# Export tool functions
async def edgar_search_tool(args: dict) -> ToolResult:
    server = RegulatoryServer()
    return await server._handle_edgar_search(args)

async def federal_register_tool(args: dict) -> ToolResult:
    server = RegulatoryServer()
    return await server._handle_federal_register(args)
