"""
Full Research Flow Simulation Test.

End-to-end test that simulates a complete research workflow with real LLM calls.
Run with: pytest tests/real/test_full_research_flow.py -v -s --log-cli-level=INFO
"""


import pytest

# ============================================================================
# Full Research Pipeline
# ============================================================================

class TestFullResearchFlow:
    """Complete research flow simulation with all components."""

    @pytest.mark.asyncio
    @pytest.mark.real_api
    @pytest.mark.slow
    async def test_complete_pipeline(self, llm_provider, llm_config, logger):
        """Test complete research pipeline: Route → Plan → Research → Consensus → Synthesize."""
        logger.info("=" * 70)
        logger.info("FULL RESEARCH PIPELINE SIMULATION")
        logger.info("=" * 70)

        query = "What are the economic impacts of AI on the job market?"
        print(f"\n🔬 Research Query: {query}\n")

        # ==========================================
        # Step 1: Intention Router
        # ==========================================
        logger.info("Step 1: Intention Routing")
        from services.orchestrator.core.router import IntentionRouter

        router = IntentionRouter()
        path = await router.route(query)

        print(f"📍 Selected Path: {path}")
        assert path in ["A", "B", "C", "D"]

        # ==========================================
        # Step 2: Planner Node
        # ==========================================
        logger.info("Step 2: Query Decomposition")
        from services.orchestrator.nodes.planner import planner_node

        state = {"query": query, "path": path}
        state = await planner_node(state)

        print(f"\n📋 Sub-queries: {len(state.get('sub_queries', []))}")
        for i, sq in enumerate(state.get('sub_queries', [])[:5], 1):
            print(f"   {i}. {sq}")

        print(f"\n💡 Hypotheses: {len(state.get('hypotheses', []))}")
        for i, h in enumerate(state.get('hypotheses', [])[:3], 1):
            print(f"   {i}. {h}")

        # ==========================================
        # Step 3: Research (Search + Scrape)
        # ==========================================
        logger.info("Step 3: Gathering Information")
        from mcp_servers.search_server.tools.academic_search import academic_search_tool
        from mcp_servers.search_server.tools.web_search import web_search_tool

        # Web search for each sub-query
        facts = []
        sources = []

        for sq in state.get('sub_queries', [])[:2]:  # Limit to avoid rate limits
            search_result = await web_search_tool({"query": sq, "max_results": 3})
            if not search_result.isError:
                facts.append({"text": search_result.content[0].text[:500], "source": "web"})
                sources.append({"type": "web", "query": sq})

        # Academic search
        academic_result = await academic_search_tool({
            "query": query,
            "source": "arxiv",
            "max_results": 2
        })
        if not academic_result.isError:
            facts.append({"text": academic_result.content[0].text[:500], "source": "arxiv"})
            sources.append({"type": "arxiv"})

        state["facts"] = facts
        state["sources"] = sources

        print(f"\n📚 Collected: {len(facts)} facts from {len(sources)} sources")

        # ==========================================
        # Step 4: Keeper Check
        # ==========================================
        logger.info("Step 4: Keeper - Context Check")
        from services.orchestrator.nodes.keeper import keeper_node

        state["iteration"] = 0
        state["max_iterations"] = 2
        state = await keeper_node(state)

        print(f"\n🛡️ Keeper: Continue={state.get('should_continue')}, Iteration={state.get('iteration')}")

        # ==========================================
        # Step 5: Consensus Engine
        # ==========================================
        logger.info("Step 5: Adversarial Consensus")
        from services.orchestrator.core.consensus import ConsensusEngine

        engine = ConsensusEngine(max_rounds=2)
        consensus_result = await engine.reach_consensus(query, facts, sources)

        print(f"\n⚖️ Consensus: {consensus_result['rounds']} rounds, Verdict={consensus_result['final_verdict']}")
        print(f"   Confidence: {consensus_result['confidence']:.2f}")

        state["generator_output"] = consensus_result["final_answer"]
        state["confidence"] = consensus_result["confidence"]

        # ==========================================
        # Step 6: Synthesizer
        # ==========================================
        logger.info("Step 6: Final Synthesis")
        from services.orchestrator.nodes.synthesizer import synthesizer_node

        state = await synthesizer_node(state)

        print("\n📝 FINAL REPORT:")
        print("-" * 60)
        print(state.get("report", "No report generated")[:1500])
        print("-" * 60)

        # Assertions
        assert state.get("report"), "Should generate report"
        assert len(state.get("report", "")) > 100, "Report should be substantial"
        assert state.get("status") == "complete"

        logger.info("✅ Full research pipeline completed successfully")

    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_path_a_memory_fork(self, llm_provider, llm_config, logger):
        """Test Path A: Incremental research with prior context."""
        logger.info("Testing Path A: Memory Fork")

        from services.orchestrator.core.router import IntentionRouter

        router = IntentionRouter()

        # Query with prior context
        query = "Continue analyzing the AI job market, expand on automation risks"
        context = {"prior_research": True}

        path = await router.route(query, context)
        print(f"\n📍 Path A query routed to: {path}")

        # A or D are acceptable
        assert path in ["A", "D"]

    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_path_c_meta_analysis(self, llm_provider, llm_config, logger):
        """Test Path C: Meta-analysis across sources."""
        logger.info("Testing Path C: Grand Synthesis")

        from services.orchestrator.core.router import IntentionRouter

        router = IntentionRouter()

        # Meta-analysis query
        query = "Compare studies on remote work productivity across different industries"

        path = await router.route(query)
        print(f"\n📍 Meta-analysis query routed to: {path}")

        # Should be C (meta-analysis) or D (deep research)
        assert path in ["C", "D"]

    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_path_b_verification(self, llm_provider, llm_config, logger):
        """Test Path B: Verification/recalculation."""
        logger.info("Testing Path B: Shadow Lab")

        from services.orchestrator.core.router import IntentionRouter

        router = IntentionRouter()

        # Verification query
        query = "Verify the claim that 47% of jobs are at risk of automation"

        path = await router.route(query)
        print(f"\n📍 Verification query routed to: {path}")

        # Should be B (verification) or D
        assert path in ["B", "D"]


# ============================================================================
# Consensus Engine Tests
# ============================================================================

class TestConsensusEngine:
    """Test adversarial collaboration."""

    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_generator_critic_judge(self, llm_provider, llm_config, logger):
        """Test Generator → Critic → Judge flow."""
        logger.info("Testing Generator/Critic/Judge agents")

        from services.orchestrator.agents.critic import CriticAgent
        from services.orchestrator.agents.generator import GeneratorAgent
        from services.orchestrator.agents.judge import JudgeAgent

        query = "What are the benefits of renewable energy?"
        facts = [
            {"text": "Solar energy costs have dropped 89% since 2010"},
            {"text": "Wind power now provides 10% of US electricity"},
            {"text": "EVs reduce carbon emissions by 50% compared to gas cars"},
        ]
        sources = [{"type": "research"}]

        # Generator
        generator = GeneratorAgent()
        answer = await generator.generate(query, facts, sources)
        print(f"\n🤠 Generator:\n{answer[:500]}...")
        assert len(answer) > 50

        # Critic
        critic = CriticAgent()
        critique = await critic.critique(answer, facts, sources)
        print(f"\n🧐 Critic:\n{critique[:500]}...")
        assert len(critique) > 50

        # Judge
        judge = JudgeAgent()
        judgment = await judge.judge(query, answer, critique)
        print(f"\n⚖️ Judge: {judgment['verdict']} (Confidence: {judgment['confidence']:.2f})")
        assert judgment['verdict'] in ["Accept", "Revise", "Reject"]
        assert 0.0 <= judgment['confidence'] <= 1.0


# ============================================================================
# Node Tests
# ============================================================================

class TestOrchestratorNodes:
    """Test individual orchestrator nodes."""

    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_planner_decomposition(self, llm_provider, llm_config, logger):
        """Test planner decomposes complex queries."""
        from services.orchestrator.nodes.planner import planner_node

        state = {
            "query": "Analyze the impact of cryptocurrency regulations on financial markets globally"
        }

        result = await planner_node(state)

        print(f"\n📋 Sub-queries: {result.get('sub_queries', [])}")
        print(f"💡 Hypotheses: {result.get('hypotheses', [])}")

        assert "sub_queries" in result
        assert len(result.get("sub_queries", [])) >= 1

    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_keeper_continuation(self, llm_provider, llm_config, logger):
        """Test keeper decides continuation correctly."""
        from services.orchestrator.nodes.keeper import keeper_node

        # Should continue (few facts)
        state = {
            "query": "AI impact",
            "facts": [{"text": "AI is growing"}],
            "iteration": 0,
            "max_iterations": 3,
        }

        result = await keeper_node(state)
        print(f"\n🛡️ Keeper (1 fact): Continue={result.get('should_continue')}")
        assert result.get("should_continue") == True

        # Should stop (max iterations)
        state["iteration"] = 3
        result = await keeper_node(state)
        print(f"🛡️ Keeper (max iter): Continue={result.get('should_continue')}")
        assert result.get("should_continue") == False

    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_divergence_alternatives(self, llm_provider, llm_config, logger):
        """Test divergence engine generates alternatives."""
        from services.orchestrator.nodes.divergence import divergence_node

        state = {
            "query": "Electric vehicles are better for the environment",
            "hypotheses": ["EVs produce zero emissions", "EVs will dominate by 2030"],
            "facts": [{"text": "EV sales grew 40% in 2024"}],
        }

        result = await divergence_node(state)

        print(f"\n🔀 Alternative Hypotheses:\n{result.get('alternative_hypotheses', 'None')[:500]}")
        assert result.get("divergence_complete") == True

    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_synthesizer_report(self, llm_provider, llm_config, logger):
        """Test synthesizer generates final report."""
        from services.orchestrator.nodes.synthesizer import synthesizer_node

        state = {
            "query": "What is machine learning?",
            "facts": [
                {"text": "ML is a subset of AI"},
                {"text": "ML learns from data patterns"},
                {"text": "Deep learning uses neural networks"},
            ],
            "sources": [{"url": "example.com"}],
            "generator_output": "Machine learning is a technology...",
        }

        result = await synthesizer_node(state)

        print(f"\n📝 Report:\n{result.get('report', 'None')[:800]}")
        print(f"📊 Confidence: {result.get('confidence', 0):.2f}")

        assert result.get("report")
        assert len(result.get("report", "")) > 50
        assert result.get("status") == "complete"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--log-cli-level=INFO"])
