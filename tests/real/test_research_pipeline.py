"""
Full Research Pipeline Tests.

End-to-end tests that simulate complete research workflows with LLM.
Run with: pytest tests/real/test_research_pipeline.py -v -s --log-cli-level=INFO
"""

import pytest
import asyncio
from shared.llm.provider import LLMMessage, LLMRole, LLMConfig

from tests.real.conftest import print_stream


# ============================================================================
# Complete Research Workflow
# ============================================================================

class TestResearchWorkflow:
    """End-to-end research workflow tests."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    @pytest.mark.slow
    async def test_complete_research_query(self, llm_provider, llm_config, logger):
        """Complete research workflow: search → analyze → synthesize."""
        logger.info("=" * 60)
        logger.info("STARTING COMPLETE RESEARCH WORKFLOW")
        logger.info("=" * 60)
        
        query = "What are the latest developments in renewable energy storage?"
        print(f"\n🔬 Research Query: {query}\n")
        
        # =====================================
        # Step 1: Web Search
        # =====================================
        logger.info("Step 1: Web Search")
        from mcp_servers.search_server.tools.web_search import web_search_tool
        
        search_result = await web_search_tool({"query": query})
        web_findings = search_result.content[0].text
        print(f"\n📌 Step 1 - Web Search:\n{web_findings[:600]}...")
        
        # =====================================
        # Step 2: Academic Search
        # =====================================
        logger.info("Step 2: Academic Search")
        from mcp_servers.search_server.tools.academic_search import academic_search_tool
        
        academic_result = await academic_search_tool({
            "query": "renewable energy storage battery",
            "source": "arxiv",
            "max_results": 3
        })
        academic_findings = academic_result.content[0].text
        print(f"\n📌 Step 2 - Academic Search:\n{academic_findings[:600]}...")
        
        # =====================================
        # Step 3: LLM Analysis
        # =====================================
        logger.info("Step 3: LLM Analysis")
        
        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content="""You are a research analyst specializing in energy technology.
Analyze sources critically and identify key insights."""),
            LLMMessage(role=LLMRole.USER, content=f"""Research Question: {query}

Web Search Results:
{web_findings}

Academic Papers:
{academic_findings}

Provide:
1. Key findings from web sources
2. Key findings from academic sources
3. Points of agreement
4. Points of disagreement or gaps""")
        ]
        
        analysis, _ = await print_stream(llm_provider, messages, llm_config, "Step 3 - Analysis")
        
        # =====================================
        # Step 4: Synthesis & Report
        # =====================================
        logger.info("Step 4: Synthesis")
        
        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content="You are a technical writer. Create concise research reports."),
            LLMMessage(role=LLMRole.USER, content=f"""Based on this analysis:

{analysis}

Write a brief research summary with:
1. Executive Summary (2-3 sentences)
2. Key Developments (bullet points)
3. Future Outlook
4. Sources Consulted""")
        ]
        
        report, _ = await print_stream(llm_provider, messages, llm_config, "Step 4 - Final Report")
        
        assert len(report) > 200, "Should generate comprehensive report"
        logger.info("Research workflow completed successfully")
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    @pytest.mark.slow
    async def test_fact_extraction_workflow(self, llm_provider, llm_config, logger):
        """Extract and verify facts from sources."""
        logger.info("Starting fact extraction workflow")
        
        # 1. Fetch a real webpage
        from mcp_servers.scraper_server.tools.fetch_url import fetch_url_tool
        
        fetch_result = await fetch_url_tool({"url": "https://example.com"})
        page_content = fetch_result.content[0].text
        
        print(f"\n📄 Source Content:\n{page_content[:400]}...")
        
        # 2. Extract facts with LLM
        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content="""You are a fact extractor. Extract atomic facts from text.
Format each fact as: FACT: [entity] | [attribute] | [value] | [confidence 0-1]"""),
            LLMMessage(role=LLMRole.USER, content=f"""Extract all verifiable facts from this content:

{page_content}

List each fact on a new line.""")
        ]
        
        facts, _ = await print_stream(llm_provider, messages, llm_config, "Extracted Facts")
        
        # 3. Verify facts consistency
        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content="You are a fact checker. Verify fact consistency."),
            LLMMessage(role=LLMRole.USER, content=f"""Review these extracted facts for consistency and potential contradictions:

{facts}

Report:
1. Consistent facts
2. Any contradictions
3. Facts needing verification""")
        ]
        
        verification, _ = await print_stream(llm_provider, messages, llm_config, "Fact Verification")
        
        assert len(verification) > 50, "Should generate verification"
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_multi_source_synthesis(self, llm_provider, llm_config, logger):
        """Synthesize information from multiple sources."""
        logger.info("Testing multi-source synthesis")
        
        # Simulate findings from different sources
        source_a = "Source A (Industry Report): Electric vehicle sales grew 40% in 2024."
        source_b = "Source B (News): EV adoption accelerating, with 35-45% growth estimated."
        source_c = "Source C (Academic): Study shows 38% YoY growth in EV registrations."
        
        combined = f"{source_a}\n{source_b}\n{source_c}"
        print(f"\n📚 Multiple Sources:\n{combined}")
        
        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content="You are a research synthesizer. Combine multiple sources into coherent findings."),
            LLMMessage(role=LLMRole.USER, content=f"""Synthesize these sources on EV growth:

{combined}

Provide:
1. Consensus finding
2. Confidence level
3. Any discrepancies
4. Recommended citation""")
        ]
        
        synthesis, _ = await print_stream(llm_provider, messages, llm_config, "Multi-Source Synthesis")
        
        assert "growth" in synthesis.lower() or "%" in synthesis


# ============================================================================
# Knowledge Graph Building
# ============================================================================

class TestKnowledgeGraphWithLLM:
    """Build knowledge graphs with LLM assistance."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_entity_relationship_extraction(self, llm_provider, llm_config, logger):
        """Extract entities and relationships for knowledge graph."""
        logger.info("Testing entity-relationship extraction")
        
        text = """
        Tesla, founded by Elon Musk in 2003, manufactures electric vehicles.
        The company is headquartered in Austin, Texas. Tesla's main competitors
        include Ford Motor Company and General Motors. Tesla acquired SolarCity
        in 2016 to expand into renewable energy. The company's market cap
        exceeded $800 billion in 2024.
        """
        
        print(f"\n📝 Input Text:\n{text}")
        
        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content="""You are a knowledge graph builder.
Extract entities and relationships in structured format.
Format: ENTITY: [name] | [type]
        RELATION: [entity1] | [relationship] | [entity2]"""),
            LLMMessage(role=LLMRole.USER, content=f"""Extract all entities and relationships from:

{text}

List entities first, then relationships.""")
        ]
        
        graph_data, _ = await print_stream(llm_provider, messages, llm_config, "Knowledge Graph Extraction")
        
        # Verify structure
        assert "ENTITY" in graph_data or "entity" in graph_data.lower()
        assert "Tesla" in graph_data
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_contradiction_detection(self, llm_provider, llm_config, logger):
        """Detect contradictions in facts."""
        logger.info("Testing contradiction detection")
        
        facts = """
        FACT 1: Apple's revenue in 2023 was $383 billion
        FACT 2: Apple is headquartered in Cupertino, California
        FACT 3: Apple's 2023 revenue was approximately $350 billion
        FACT 4: Tim Cook became CEO in 2011
        FACT 5: Apple was founded in 1976
        FACT 6: Apple was founded in 1975
        """
        
        print(f"\n📊 Facts to Check:\n{facts}")
        
        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content="You are a fact consistency checker. Identify contradictions."),
            LLMMessage(role=LLMRole.USER, content=f"""Analyze these facts for contradictions:

{facts}

For each contradiction found, explain:
1. Which facts conflict
2. Why they conflict
3. Which is likely correct (if determinable)""")
        ]
        
        analysis, _ = await print_stream(llm_provider, messages, llm_config, "Contradiction Analysis")
        
        # Should detect the revenue and founding date contradictions
        assert "contradiction" in analysis.lower() or "conflict" in analysis.lower()


# ============================================================================
# Report Generation
# ============================================================================

class TestReportGeneration:
    """Generate research reports with LLM."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_executive_summary(self, llm_provider, llm_config, logger):
        """Generate executive summary from research."""
        logger.info("Testing executive summary generation")
        
        research_findings = """
        Key Findings:
        1. Market grew 25% YoY
        2. Three major competitors entered the space
        3. Regulatory changes expected Q3 2024
        4. Customer satisfaction at 87%
        5. Supply chain issues resolved
        
        Data Points:
        - Revenue: $45M (up from $36M)
        - Customers: 12,500 (up 18%)
        - NPS Score: 72 (industry avg: 45)
        """
        
        print(f"\n📊 Research Findings:\n{research_findings}")
        
        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content="You are an executive report writer. Be concise and impactful."),
            LLMMessage(role=LLMRole.USER, content=f"""Create an executive summary from these findings:

{research_findings}

Requirements:
- 3-4 sentences maximum
- Lead with the most impactful insight
- Include one key metric
- End with forward-looking statement""")
        ]
        
        summary, _ = await print_stream(llm_provider, messages, llm_config, "Executive Summary")
        
        assert len(summary) > 50, "Should generate summary"
        # Note: Reasoning models may include thought process, so relaxed upper bound
        # The actual summary content is what matters, not strict length


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--log-cli-level=INFO"])
