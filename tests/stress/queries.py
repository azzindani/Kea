"""
Stress Test Queries.

20 massive-scale research queries designed to push Project to its limits.
"""

from dataclasses import dataclass


@dataclass
class StressQuery:
    """A stress test query definition."""
    id: int
    name: str
    prompt: str
    expected_tool_iterations: int  # Rough estimate
    expected_llm_calls: int  # Should be << tool_iterations
    builds_database: bool = False
    spawns_agents: bool = False


QUERIES: list[StressQuery] = [
    # =========================================================================
    # Financial & Quantitative Analysis
    # =========================================================================
    StressQuery(
        id=1,
        name="Indonesian Alpha Hunt",
        prompt="""Analyze ALL companies on the Indonesian Stock Exchange (IDX). Filter for market cap <5T IDR, >20% YoY revenue growth, <10 P/E ratio. For ALL matching candidates, scrape their Annual Reports for the last 10 years. Perform automated DuPont analysis on each. Predict which ones have the highest probability of being 'Multibaggers' in 2026 based on CAPEX expansion. Build a database of all findings. Output ranked entry/exit points.""",
        expected_tool_iterations=5000,
        expected_llm_calls=50,
        builds_database=True,
    ),
    StressQuery(
        id=2,
        name="Bryan Johnson Blueprint",
        prompt="""Map the COMPLETE investment portfolio and ALL public affiliations of Bryan Johnson (Blueprint/Kernel) going back to 2010. Scrape LinkedIn, Crunchbase, SEC filings, press releases, and patent databases. Identify every company in Life Science/Longevity that shares ANY connection (board, VC, patents, advisors, employees). Build a knowledge graph with 10,000+ nodes. Triangulate to find proxy investment opportunities.""",
        expected_tool_iterations=10000,
        expected_llm_calls=100,
        builds_database=True,
    ),
    StressQuery(
        id=3,
        name="Big Short 2.0",
        prompt="""Scrape the last 15 years of 13F filings for Michael Burry, Bill Ackman, David Einhorn, and 20 other notable contrarian investors. Cross-reference with TSMC Taiwan export data (monthly since 2010), GPU channel inventory, and DRAM/NAND spot prices. Build a comprehensive macro correlation model. Generate a full thesis with probabilistic risk assessment for semiconductor positions through 2027.""",
        expected_tool_iterations=8000,
        expected_llm_calls=80,
        builds_database=True,
    ),
    StressQuery(
        id=4,
        name="Rare Earth Supply Chain",
        prompt="""Trace the COMPLETE global supply chain of Neodymium, Dysprosium, and Praseodymium from every known mine to every major EV/wind turbine manufacturer. Scrape mining permits, export records, shipping manifests (where public), and corporate filings for all companies in the chain. Build a dependency graph with 5,000+ companies. Identify all choke points vulnerable to trade wars. Output with financial health scores.""",
        expected_tool_iterations=5000,
        expected_llm_calls=50,
        builds_database=True,
    ),
    
    # =========================================================================
    # Legal & Regulatory
    # =========================================================================
    StressQuery(
        id=5,
        name="Putusan MA Builder",
        prompt="""Navigate the Mahkamah Agung (Indonesian Supreme Court) website. Systematically download ALL available court decisions for 'Sengketa Tanah' (Land Disputes) from 2000 to 2025. Target: 50,000+ PDFs. Extract 'Pertimbangan Hakim' section from each. Build a searchable vector database (Qdrant). Create embeddings for semantic search. Upload dataset to HuggingFace. Generate summary statistics by year, court region, and outcome type.""",
        expected_tool_iterations=50000,
        expected_llm_calls=100,
        builds_database=True,
    ),
    StressQuery(
        id=6,
        name="Canadian Regulation Spider",
        prompt="""Scrape the COMPLETE Canadian Federal Environmental Regulatory framework from Justice Laws Website. Download ALL acts, regulations, and amendments related to: Carbon Pricing, Oil Sands, Mining, Water Protection, Species at Risk, Environmental Assessment — going back to 1970. Build a hierarchical knowledge base linking Act → Regulations → Amendments → Court Interpretations. Verify all cross-references. Output as searchable database.""",
        expected_tool_iterations=10000,
        expected_llm_calls=80,
        builds_database=True,
    ),
    StressQuery(
        id=7,
        name="Clinical Trials Meta-Study",
        prompt="""Search ClinicalTrials.gov for ALL Phase 2/3/4 trials for mRNA therapies (vaccines, cancer, rare diseases) — entire database since 2010. Target: 5,000+ trials. For terminated/suspended trials, find corresponding sponsor communications. Link with academic publications and patent filings. Build a comprehensive database classifying failure modes. Statistical analysis of success factors.""",
        expected_tool_iterations=5000,
        expected_llm_calls=60,
        builds_database=True,
    ),
    StressQuery(
        id=8,
        name="No Way Out Scenario",
        prompt="""Research ALL legal cases involving conflicts between EU data protection (GDPR, AI Act) and US enforcement (CLOUD Act, FISA 702) from 2018 to present. Scrape court records from EU Court of Justice, Irish DPC, and US Federal Courts. Build a precedent database. For each conflict pattern, construct legal arguments. Identify unresolvable deadlocks. Propose legislative amendments with supporting reasoning.""",
        expected_tool_iterations=3000,
        expected_llm_calls=50,
        builds_database=True,
    ),
    
    # =========================================================================
    # Investigation & Verification
    # =========================================================================
    StressQuery(
        id=9,
        name="Dark Money Trace",
        prompt="""Investigate Tether (USDT), Circle (USDC), Binance, and the top 20 crypto entities. Scrape ALL available: SEC/CFTC filings, NYAG documents, Senate hearing transcripts, corporate registries (HK, BVI, Cayman, Delaware, Singapore), offshore leaks databases. Build a knowledge graph connecting executives, banking partners, corporate structures, and fund flows. Flag all entities with regulatory issues. Historical timeline 2014-present.""",
        expected_tool_iterations=15000,
        expected_llm_calls=100,
        builds_database=True,
    ),
    StressQuery(
        id=10,
        name="Disinfo Hunter",
        prompt="""Trace the origin and propagation of 10 major disinformation narratives: Solar Maximum, 5G health, vaccine microchips, election fraud claims, climate denial, deepfake politicians, AI extinction, etc. For each: find first appearance, map spread across all major platforms (archived), categorize sources, score credibility, cross-reference with scientific sources. Build a comprehensive debunking database with timeline visualization data.""",
        expected_tool_iterations=8000,
        expected_llm_calls=80,
        builds_database=True,
    ),
    
    # =========================================================================
    # Scientific & Academic
    # =========================================================================
    StressQuery(
        id=11,
        name="Room-Temp Superconductor Verification",
        prompt="""Collect ALL academic papers from arXiv, PubMed, and Semantic Scholar related to room-temperature superconductivity claims (last 20 years). Include LK-99, carbonaceous sulfur hydride, and all related materials. Extract: claimed materials, synthesis methods, measurement conditions, replication attempts. Build a knowledge graph of claims vs. refutations. Generate consensus report with specific physics reasoning.""",
        expected_tool_iterations=3000,
        expected_llm_calls=50,
        builds_database=True,
    ),
    StressQuery(
        id=12,
        name="Mars Colony Logistics",
        prompt="""Calculate complete logistical requirements for a Mars colony scaling from 10 to 10,000 humans over 50 years. Model consumption curves for O2, water, food, energy, manufacturing supplies. Scrape SpaceX, Blue Origin, NASA, ESA, and academic sources for all available payload and cost data. Model failure scenarios (hydroponics, life support, resupply delays). Build interactive simulation database. Output phased budget projections.""",
        expected_tool_iterations=2000,
        expected_llm_calls=40,
        builds_database=True,
    ),
    StressQuery(
        id=13,
        name="Global Arbitrage",
        prompt="""Track the price of PlayStation 5 Pro, iPhone 16 Pro Max, and NVIDIA RTX 5090 across 50 countries. Scrape official stores, Amazon regional sites, local e-commerce (Tokopedia, Mercado Libre, Flipkart, etc.). Collect historical prices for the last 2 years where available. Convert using live and historical forex. Calculate arbitrage spreads including shipping, customs, and taxes for all viable routes. Build a trading opportunity database.""",
        expected_tool_iterations=5000,
        expected_llm_calls=50,
        builds_database=True,
    ),
    
    # =========================================================================
    # Strategic Intelligence
    # =========================================================================
    StressQuery(
        id=14,
        name="Pharma Pipeline Analyzer",
        prompt="""Download the COMPLETE FDA drug database (CDER, CBER) — all submissions, approvals, rejections, warnings since 2000. Cross-reference with ClinicalTrials.gov, SEC filings for pharma companies, and patent databases. Build a comprehensive pipeline tracker: every drug, every company, every milestone. Predict approval probabilities using historical patterns. Output investment thesis for biotech sector.""",
        expected_tool_iterations=20000,
        expected_llm_calls=100,
        builds_database=True,
    ),
    StressQuery(
        id=15,
        name="Geopolitical Risk Index",
        prompt="""Build a comprehensive Taiwan geopolitical risk index. Aggregate news from 50 sources (Reuters, Bloomberg, SCMP, Global Times, Taipei Times, Nikkei, defense publications, etc.) for the last 25 years. Classify by risk category (military, economic, diplomatic, technology). Correlate with market movements (TAIEX, SOX, VIX). Build predictive model. Historical validation against actual events (2019-present).""",
        expected_tool_iterations=100000,
        expected_llm_calls=200,
        builds_database=True,
    ),
    StressQuery(
        id=16,
        name="Academic Grant Network",
        prompt="""Scrape NSF, NIH, DOE, DARPA, and EU Horizon award databases. Download ALL grants >$100K related to AI, ML, robotics since 2010. Target: 100,000+ grants. Build database: PI, institution, amount, topic, duration, outcomes. Network analysis: identify top institutions, prolific PIs, funding trends. Predict emerging research areas based on recent grant patterns.""",
        expected_tool_iterations=100000,
        expected_llm_calls=200,
        builds_database=True,
    ),
    StressQuery(
        id=17,
        name="Startup Due Diligence",
        prompt="""Conduct COMPREHENSIVE due diligence on Anthropic, OpenAI, xAI, Mistral, and Cohere. For each: ALL funding rounds, ALL investors (Crunchbase, PitchBook), ALL patent filings (USPTO, EPO), ALL job postings (historical since founding), ALL press/blog posts, ALL regulatory filings, ALL executive backgrounds (LinkedIn, news). Cross-reference claims with evidence. Build verification matrix. Output institutional-grade investor memo for each.""",
        expected_tool_iterations=10000,
        expected_llm_calls=100,
        builds_database=True,
    ),
    StressQuery(
        id=18,
        name="Policy Impact Simulator",
        prompt="""Research ALL major AI/tech regulations globally: EU AI Act, US Executive Order, UK framework, China regulations, Japan, Korea, Singapore, Brazil. Collect full text of every regulation, proposal, and amendment. Map which companies affected by which provisions. Model compliance costs based on 10-K filings and public statements. Scenario simulation for different regulatory futures. Output decision support matrix.""",
        expected_tool_iterations=5000,
        expected_llm_calls=60,
        builds_database=True,
    ),
    StressQuery(
        id=19,
        name="Competitive Intelligence Report",
        prompt="""Deep analysis of AI strategy for: Google, Microsoft, Meta, Amazon, Apple, NVIDIA, AMD, Intel, Qualcomm, Tesla. For each: ALL earnings calls (10 years), ALL AI press releases, ALL AI patents, ALL AI acquisitions, ALL AI job postings (archived). Build capability matrix. Predict market positioning through 2030. Identify M&A opportunities and competitive threats.""",
        expected_tool_iterations=20000,
        expected_llm_calls=150,
        builds_database=True,
    ),
    StressQuery(
        id=20,
        name="Research Synthesis Swarm",
        prompt="""Produce a 100-page comprehensive report: 'The State of Nuclear Fusion Energy 2025'. Spawn 5 parallel research agents with FULL autonomy:
- Agent 1: Technical (ITER, NIF, ALL private fusion companies worldwide)
- Agent 2: Economic (historical + projected costs, ALL investments since 2000)
- Agent 3: Policy (government funding for ALL countries with fusion programs)
- Agent 4: Environmental (lifecycle analysis, ALL published studies)
- Agent 5: Competition (detailed comparison with ALL energy alternatives)
Each agent generates 15-20 pages with full citations from 500+ sources total. Editor agent synthesizes, cross-references, resolves contradictions. Final output: publication-quality report.""",
        expected_tool_iterations=5000,
        expected_llm_calls=100,
        builds_database=True,
        spawns_agents=True,
    ),
]


def get_query(query_id: int) -> StressQuery | None:
    """Get a query by ID."""
    for q in QUERIES:
        if q.id == query_id:
            return q
    return None


def list_queries() -> list[StressQuery]:
    """List all available queries."""
    return QUERIES
