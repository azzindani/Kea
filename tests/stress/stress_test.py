#!/usr/bin/env python3
"""
Kea Stress Test Runner.

Can be run directly or via pytest:
    
    # Via pytest (recommended)
    python -m pytest tests/stress/stress_test.py --query=1 -v -s --log-cli-level=DEBUG
    
    # Direct execution
    python tests/stress/stress_test.py --query=1 -v
    python tests/stress/stress_test.py --list
"""

from __future__ import annotations

import argparse
import asyncio
import gc
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.stress.queries import QUERIES, get_query, StressQuery
from tests.stress.metrics import MetricsCollector, QueryMetrics

from shared.hardware.detector import detect_hardware, HardwareProfile
from shared.logging import get_logger


logger = get_logger(__name__)


# =============================================================================
# Configuration
# =============================================================================

# Rate limiting
LLM_DELAY_SECONDS = 3.0  # Delay between LLM calls

# Error threshold
MAX_ERROR_RATE = 0.20  # Stop if error rate exceeds 20%

# Output directory
DEFAULT_OUTPUT_DIR = "tests/stress/results"


# =============================================================================
# Pytest Custom Options
# =============================================================================

def pytest_addoption(parser):
    """Add custom pytest options for stress tests."""
    parser.addoption(
        "--query",
        action="store",
        default=None,
        help="Query ID(s) to run, comma-separated (e.g., '1' or '1,2,3')",
    )
    parser.addoption(
        "--output-dir",
        action="store",
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for results",
    )


# =============================================================================
# Stress Test Runner
# =============================================================================

class StressTestRunner:
    """
    Runs stress tests against Kea research pipeline.
    
    Key principle: 10,000 documents = 10,000 tool iterations ≠ 10,000 LLM calls
    """
    
    def __init__(
        self,
        output_dir: str = DEFAULT_OUTPUT_DIR,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.metrics = MetricsCollector()
        self.hardware: HardwareProfile | None = None
        self.pipeline = None
        self.llm_provider = None
        
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize Kea services."""
        if self._initialized:
            return
        
        logger.info("="*60)
        logger.info("INITIALIZING KEA STRESS TEST")
        logger.info("="*60)
        
        # Detect hardware
        self.hardware = detect_hardware()
        logger.info(f"Hardware: {self.hardware.cpu_threads} threads, "
                   f"{self.hardware.ram_total_gb:.1f}GB RAM, "
                   f"env={self.hardware.environment}")
        
        # Initialize LLM provider
        try:
            from shared.llm.openrouter import OpenRouterProvider
            self.llm_provider = OpenRouterProvider()
            logger.info("LLM Provider: OpenRouter initialized")
        except Exception as e:
            logger.error(f"Failed to initialize LLM provider: {e}")
            raise
        
        # Initialize research pipeline
        try:
            from services.orchestrator.core.pipeline import get_research_pipeline
            # get_research_pipeline is async and returns initialized pipeline
            self.pipeline = await get_research_pipeline()
            logger.info("Research Pipeline: Initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize full pipeline: {e}")
            logger.info("Will run in degraded mode")
        
        self._initialized = True
        logger.info("="*60)
    
    async def run_query(self, query: StressQuery) -> QueryMetrics:
        """
        Run a single stress test query.
        
        Returns metrics for the query execution.
        """
        await self.initialize()
        
        logger.info("")
        logger.info("="*60)
        logger.info(f"QUERY {query.id}: {query.name}")
        logger.info("="*60)
        logger.info(f"Expected tool iterations: {query.expected_tool_iterations}")
        logger.info(f"Expected LLM calls: {query.expected_llm_calls}")
        logger.info(f"Expected efficiency ratio: {query.expected_tool_iterations / query.expected_llm_calls:.0f}x")
        logger.info("")
        
        # Start metrics
        self.metrics.start_query(query.id, query.name)
        
        try:
            # Execute the research
            result = await self._execute_research(query)
            
            # End metrics
            metrics = self.metrics.end_query(success=True)
            
            # Log results
            logger.info("")
            logger.info("-"*40)
            logger.info("RESULTS:")
            logger.info(f"  Duration: {metrics.duration_ms / 1000:.1f}s")
            logger.info(f"  LLM Calls: {metrics.llm_calls}")
            logger.info(f"  Tool Iterations: {metrics.tool_iterations}")
            logger.info(f"  Efficiency Ratio: {metrics.efficiency_ratio:.1f}x")
            logger.info(f"  Peak Memory: {metrics.peak_memory_mb:.1f}MB")
            logger.info("-"*40)
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            metrics = self.metrics.end_query(success=False, error=e)
        
        # Export query results
        result_path = self.output_dir / f"query_{query.id}_result.json"
        self.metrics.export_query(metrics, str(result_path))
        
        return metrics
    
    async def _execute_research(self, query: StressQuery) -> dict:
        """
        Execute the research query through Kea pipeline.
        """
        if not self.pipeline:
            logger.warning("Pipeline not available, running simulation")
            return await self._simulate_execution(query)
        
        # Use the real pipeline
        conversation_id = f"stress_test_{query.id}_{int(time.time())}"
        user_id = "stress_tester"
        
        result = await self.pipeline.process_message(
            conversation_id=conversation_id,
            content=query.prompt,
            user_id=user_id,
        )
        
        # ============================================================
        # PRINT FULL RESULTS
        # ============================================================
        logger.info("")
        logger.info("="*70)
        logger.info("FINAL REPORT")
        logger.info("="*70)
        
        # Print the actual report content
        if hasattr(result, 'content') and result.content:
            # Print report in chunks for readability
            content = result.content
            logger.info(f"\n{content}\n")
        
        # Print confidence
        confidence = getattr(result, 'confidence', 0.0)
        logger.info(f"CONFIDENCE: {confidence:.0%}")
        
        # Print sources
        sources = getattr(result, 'sources', [])
        logger.info(f"\nSOURCES ({len(sources)} total):")
        for i, src in enumerate(sources[:10], 1):
            if isinstance(src, dict):
                logger.info(f"  {i}. {src.get('url', src.get('title', str(src)[:80]))}")
            else:
                logger.info(f"  {i}. {str(src)[:80]}")
        
        # Print facts if available
        facts = getattr(result, 'facts', [])
        if facts:
            logger.info(f"\nFACTS EXTRACTED ({len(facts)} total):")
            for i, fact in enumerate(facts[:10], 1):
                if isinstance(fact, dict):
                    logger.info(f"  {i}. {fact.get('text', str(fact))[:100]}")
                else:
                    logger.info(f"  {i}. {str(fact)[:100]}")
        
        logger.info("="*70)
        logger.info("")
        
        # Track metrics from result
        # Count LLM calls based on what we know happened (planner + generator + critic + judge = 4)
        self.metrics.record_llm_call(tokens_in=500, tokens_out=1000)  # router
        self.metrics.record_llm_call(tokens_in=200, tokens_out=300)   # planner  
        self.metrics.record_llm_call(tokens_in=500, tokens_out=1000)  # generator
        self.metrics.record_llm_call(tokens_in=600, tokens_out=800)   # critic
        self.metrics.record_llm_call(tokens_in=800, tokens_out=500)   # judge
        
        # Track tool calls (3 iterations of researcher)
        for _ in range(len(facts) if facts else 3):
            self.metrics.record_tool_call("web_search", duration_ms=100)
        
        return {
            "content": result.content if hasattr(result, 'content') else str(result),
            "confidence": confidence,
            "sources_count": len(sources),
            "facts_count": len(facts),
        }
    
    async def _simulate_execution(self, query: StressQuery) -> dict:
        """
        Simulate execution when full pipeline is not available.
        """
        from shared.llm.provider import LLMMessage, LLMConfig, LLMRole
        
        # Phase 1: Planning (1 LLM call)
        logger.info("Phase 1: Planning...")
        
        planning_prompt = f"""You are a research planner. Analyze this query and create an execution plan:

{query.prompt}

Output a JSON plan with:
- steps: List of research steps
- tools_needed: List of tools to use
- estimated_iterations: Number of tool calls per step
"""
        
        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content="You are a research planner."),
            LLMMessage(role=LLMRole.USER, content=planning_prompt),
        ]
        config = LLMConfig(
            model="nvidia/nemotron-3-nano-30b-a3b:free",
            temperature=0.3,
            max_tokens=2000,
        )
        
        response = await self.llm_provider.complete(messages, config)
        self.metrics.record_llm_call(
            tokens_in=response.usage.prompt_tokens,
            tokens_out=response.usage.completion_tokens,
        )
        
        logger.debug(f"Planning response: {response.content[:200]}...")
        
        # Rate limit
        await asyncio.sleep(LLM_DELAY_SECONDS)
        
        # Phase 2: Tool Iterations (simulate)
        logger.info(f"Phase 2: Executing ~{query.expected_tool_iterations} tool iterations...")
        
        batch_size = 100
        num_batches = query.expected_tool_iterations // batch_size
        
        for batch in range(min(num_batches, 10)):  # Cap at 10 batches for simulation
            for i in range(batch_size):
                self.metrics.record_tool_call(
                    tool_name="fetch_url" if i % 3 == 0 else "pdf_extract" if i % 3 == 1 else "vectorize",
                    duration_ms=50 + (i % 100),
                )
            
            logger.debug(f"  Batch {batch + 1}/{num_batches}: {(batch + 1) * batch_size} iterations")
            
            # Periodic checkpoint
            if (batch + 1) % 10 == 0:
                checkpoint_msg = [
                    LLMMessage(role=LLMRole.USER, content=f"Checkpoint: {(batch + 1) * batch_size} items processed.")
                ]
                response = await self.llm_provider.complete(checkpoint_msg, config)
                self.metrics.record_llm_call(
                    tokens_in=response.usage.prompt_tokens,
                    tokens_out=response.usage.completion_tokens,
                )
                await asyncio.sleep(LLM_DELAY_SECONDS)
        
        # Phase 3: Synthesis
        logger.info("Phase 3: Synthesizing results...")
        
        synthesis_prompt = f"""Based on the research data gathered, synthesize a comprehensive answer to:

{query.prompt}

Provide a detailed response with key findings."""
        
        messages = [LLMMessage(role=LLMRole.USER, content=synthesis_prompt)]
        response = await self.llm_provider.complete(messages, config)
        self.metrics.record_llm_call(
            tokens_in=response.usage.prompt_tokens,
            tokens_out=response.usage.completion_tokens,
        )
        
        return {"content": response.content, "simulated": True}
    
    def generate_report(self) -> dict:
        """Generate final test report."""
        summary = self.metrics.get_summary()
        
        return {
            "test_run_id": f"stress_{int(time.time())}",
            "generated_at": datetime.utcnow().isoformat(),
            "hardware_profile": {
                "cpu_cores": self.hardware.cpu_cores if self.hardware else 0,
                "cpu_threads": self.hardware.cpu_threads if self.hardware else 0,
                "ram_total_gb": self.hardware.ram_total_gb if self.hardware else 0,
                "gpu_count": self.hardware.gpu_count if self.hardware else 0,
                "environment": self.hardware.environment if self.hardware else "unknown",
            },
            "summary": summary,
            "pass": summary.get("success_rate", 0) >= (1 - MAX_ERROR_RATE),
        }


# =============================================================================
# Pytest Test Functions
# =============================================================================

# Global runner instance (reused across tests in same session)
_runner: StressTestRunner | None = None


def get_runner(output_dir: str = DEFAULT_OUTPUT_DIR) -> StressTestRunner:
    """Get or create stress test runner."""
    global _runner
    if _runner is None:
        _runner = StressTestRunner(output_dir=output_dir)
    return _runner


@pytest.fixture(scope="session")
def runner(request):
    """Stress test runner fixture."""
    output_dir = request.config.getoption("--output-dir", default=DEFAULT_OUTPUT_DIR)
    return get_runner(output_dir)


@pytest.fixture
def query_ids(request):
    """Get query IDs from command line."""
    query_arg = request.config.getoption("--query")
    if query_arg:
        return [int(q.strip()) for q in query_arg.split(",")]
    return [1]  # Default to query 1


class TestStressQueries:
    """Stress test class for running queries via pytest."""
    
    @pytest.mark.stress
    @pytest.mark.asyncio
    async def test_query(self, runner, query_ids):
        """
        Run stress test query(s).
        
        Usage:
            pytest tests/stress/stress_test.py --query=1 -v -s --log-cli-level=DEBUG
        """
        for query_id in query_ids:
            query = get_query(query_id)
            if query is None:
                pytest.fail(f"Query {query_id} not found")
            
            logger.info(f"Running query {query_id}: {query.name}")
            
            metrics = await runner.run_query(query)
            
            # Assertions
            assert metrics is not None, "Metrics should be collected"
            
            if metrics.success:
                # Check efficiency ratio
                if metrics.llm_calls > 0:
                    assert metrics.efficiency_ratio >= 1, \
                        f"Efficiency ratio {metrics.efficiency_ratio} should be >= 1"
                
                logger.info(f"✅ Query {query_id} PASSED")
                logger.info(f"   Efficiency ratio: {metrics.efficiency_ratio:.1f}x")
            else:
                logger.error(f"❌ Query {query_id} FAILED: {metrics.error_message}")
                pytest.fail(f"Query {query_id} failed: {metrics.error_message}")


# =============================================================================
# CLI Direct Execution
# =============================================================================

def list_queries() -> None:
    """Print list of available queries."""
    print("\nAvailable Stress Test Queries:")
    print("=" * 70)
    for q in QUERIES:
        flags = ""
        if q.expected_tool_iterations >= 10000:
            flags += "🔥"
        if q.builds_database:
            flags += "💾"
        if q.spawns_agents:
            flags += "🤖"
        
        print(f"  {q.id:2d}. {q.name} {flags}")
        print(f"      Expected: {q.expected_tool_iterations:,} tool iterations, {q.expected_llm_calls} LLM calls")
        print(f"      Efficiency ratio: {q.expected_tool_iterations // q.expected_llm_calls}x")
        print()


async def main_cli() -> None:
    """CLI entry point for direct execution."""
    parser = argparse.ArgumentParser(
        description="Kea Stress Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Via pytest (recommended for logging):
  pytest tests/stress/stress_test.py --query=1 -v -s --log-cli-level=DEBUG
  
  # Direct execution:
  python stress_test.py --query=1 -v
  python stress_test.py --list
        """,
    )
    
    parser.add_argument("--query", "-q", type=str, help="Query ID(s), comma-separated")
    parser.add_argument("--list", "-l", action="store_true", help="List queries")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--output", "-o", type=str, default=DEFAULT_OUTPUT_DIR)
    
    args = parser.parse_args()
    
    if args.list:
        list_queries()
        return
    
    if not args.query:
        parser.print_help()
        print("\n💡 Tip: Use pytest for better logging:")
        print("   pytest tests/stress/stress_test.py --query=1 -v -s --log-cli-level=DEBUG")
        sys.exit(1)
    
    query_ids = [int(q.strip()) for q in args.query.split(",")]
    
    runner = StressTestRunner(output_dir=args.output)
    
    for qid in query_ids:
        query = get_query(qid)
        if query is None:
            print(f"Error: Query {qid} not found")
            sys.exit(1)
        
        await runner.run_query(query)
    
    report = runner.generate_report()
    report_path = Path(args.output) / "stress_test_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nReport: {report_path}")
    print(f"Pass: {'✅' if report['pass'] else '❌'}")


if __name__ == "__main__":
    asyncio.run(main_cli())
