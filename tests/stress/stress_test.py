#!/usr/bin/env python3
"""
Kea Stress Test Runner.

CLI tool to run individual stress test queries at massive scale.

Usage:
    python tests/stress/stress_test.py --query=1 -v
    python tests/stress/stress_test.py --query=1,2,3
    python tests/stress/stress_test.py --list
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.stress.queries import QUERIES, get_query, StressQuery
from tests.stress.metrics import MetricsCollector, QueryMetrics

from shared.hardware.detector import detect_hardware, HardwareProfile
from shared.logging import get_logger, setup_logging


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
        verbose: bool = False,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        
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
            self.pipeline = get_research_pipeline()
            await self.pipeline.initialize()
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
        
        This is the core execution loop that should achieve high efficiency ratio:
        - Few LLM calls for planning and synthesis
        - Many tool iterations for data gathering
        """
        if not self.pipeline:
            logger.warning("Pipeline not available, running simulation")
            return await self._simulate_execution(query)
        
        # Use the real pipeline
        from services.orchestrator.core.pipeline import ResearchResult
        
        # Create a conversation for this query
        conversation_id = f"stress_test_{query.id}_{int(time.time())}"
        user_id = "stress_tester"
        
        # This will internally:
        # 1. Classify the query (1 LLM call)
        # 2. Plan the research (1 LLM call)
        # 3. Execute tool calls in batches (many iterations, few LLM calls)
        # 4. Synthesize results (1-3 LLM calls)
        result = await self.pipeline.process_message(
            conversation_id=conversation_id,
            content=query.prompt,
            user_id=user_id,
        )
        
        return {
            "content": result.content,
            "confidence": result.confidence,
            "sources_count": len(result.sources),
        }
    
    async def _simulate_execution(self, query: StressQuery) -> dict:
        """
        Simulate execution when full pipeline is not available.
        
        Used for testing the stress test framework itself.
        """
        from shared.llm.provider import LLMMessage, LLMConfig, LLMRole
        
        # Simulate the pattern: LLM plans → tools execute → LLM synthesizes
        
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
        
        # Rate limit
        await asyncio.sleep(LLM_DELAY_SECONDS)
        
        # Phase 2: Tool Iterations (simulate based on expected)
        logger.info(f"Phase 2: Executing ~{query.expected_tool_iterations} tool iterations...")
        
        # Simulate tool calls in batches
        batch_size = 100
        num_batches = query.expected_tool_iterations // batch_size
        
        for batch in range(min(num_batches, 10)):  # Cap at 10 batches for simulation
            for i in range(batch_size):
                # Simulate tool call
                self.metrics.record_tool_call(
                    tool_name="fetch_url" if i % 3 == 0 else "pdf_extract" if i % 3 == 1 else "vectorize",
                    duration_ms=50 + (i % 100),
                )
            
            # Progress update
            if self.verbose:
                logger.info(f"  Batch {batch + 1}/{num_batches}: {(batch + 1) * batch_size} iterations")
            
            # Periodic checkpoint (every 1000 iterations = 1 LLM call)
            if (batch + 1) % 10 == 0:
                checkpoint_msg = [
                    LLMMessage(role=LLMRole.USER, content=f"Checkpoint: {(batch + 1) * batch_size} items processed. Any issues to address?")
                ]
                response = await self.llm_provider.complete(checkpoint_msg, config)
                self.metrics.record_llm_call(
                    tokens_in=response.usage.prompt_tokens,
                    tokens_out=response.usage.completion_tokens,
                )
                await asyncio.sleep(LLM_DELAY_SECONDS)
        
        # Phase 3: Synthesis (1 LLM call)
        logger.info("Phase 3: Synthesizing results...")
        
        synthesis_prompt = f"""Based on the research data gathered, synthesize a comprehensive answer to:

{query.prompt}

Provide a detailed response with key findings."""
        
        messages = [
            LLMMessage(role=LLMRole.USER, content=synthesis_prompt),
        ]
        response = await self.llm_provider.complete(messages, config)
        self.metrics.record_llm_call(
            tokens_in=response.usage.prompt_tokens,
            tokens_out=response.usage.completion_tokens,
        )
        
        return {
            "content": response.content,
            "simulated": True,
        }
    
    def generate_report(self) -> dict:
        """Generate final test report."""
        summary = self.metrics.get_summary()
        
        report = {
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
        
        return report


# =============================================================================
# CLI
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


async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Kea Stress Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python stress_test.py --query=1 -v      Run query 1 with verbose output
  python stress_test.py --query=1,2,3     Run queries 1, 2, and 3
  python stress_test.py --list            List all available queries
        """,
    )
    
    parser.add_argument(
        "--query", "-q",
        type=str,
        help="Query ID(s) to run, comma-separated (e.g., '1' or '1,2,3')",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available queries",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    if args.list:
        list_queries()
        return
    
    if not args.query:
        parser.print_help()
        print("\nError: --query is required. Use --list to see available queries.")
        sys.exit(1)
    
    # Parse query IDs
    try:
        query_ids = [int(q.strip()) for q in args.query.split(",")]
    except ValueError:
        print(f"Error: Invalid query ID format: {args.query}")
        sys.exit(1)
    
    # Validate query IDs
    for qid in query_ids:
        if get_query(qid) is None:
            print(f"Error: Query {qid} not found. Use --list to see available queries.")
            sys.exit(1)
    
    # Run the stress test
    runner = StressTestRunner(
        output_dir=args.output,
        verbose=args.verbose,
    )
    
    print(f"\n{'='*60}")
    print(f"KEA STRESS TEST")
    print(f"{'='*60}")
    print(f"Queries to run: {query_ids}")
    print(f"Output directory: {args.output}")
    print(f"{'='*60}\n")
    
    for qid in query_ids:
        query = get_query(qid)
        try:
            metrics = await runner.run_query(query)
            
            if not metrics.success:
                print(f"\n⚠️  Query {qid} FAILED: {metrics.error_message}")
        except KeyboardInterrupt:
            print("\n\nInterrupted by user.")
            break
        except Exception as e:
            print(f"\n❌ Query {qid} ERROR: {e}")
    
    # Generate final report
    report = runner.generate_report()
    report_path = Path(args.output) / "stress_test_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n{'='*60}")
    print("STRESS TEST COMPLETE")
    print(f"{'='*60}")
    print(f"Report saved to: {report_path}")
    print(f"Pass: {'✅ YES' if report['pass'] else '❌ NO'}")
    if report["summary"]:
        print(f"Overall efficiency ratio: {report['summary'].get('overall_efficiency_ratio', 0):.1f}x")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
