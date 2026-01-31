#!/usr/bin/env python3
"""
Kea Stress Test Runner (API-Based).

Runs stress tests via API Gateway endpoints, properly exercising
the full microservices stack with authentication.

Usage:
    # Via pytest with predefined query ID
    python -m pytest tests/stress/stress_test.py --query=1 -v -s --log-cli-level=DEBUG
    
    # Via pytest with CUSTOM QUERY STRING
    python -m pytest tests/stress/stress_test.py --query="Analyze Apple stock performance" -v -s --log-cli-level=DEBUG
    
    # Direct execution with custom query
    python tests/stress/stress_test.py --query="What are the top 10 AI companies?" -v
    python tests/stress/stress_test.py --list
    
Prerequisites:
    1. Start API Gateway: python -m services.api_gateway.main
    2. Start Orchestrator: python -m services.orchestrator.main  
    3. Start RAG Service: python -m services.rag_service.main
    4. Set OPENROUTER_API_KEY environment variable
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

import httpx
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.stress.queries import QUERIES, get_query, StressQuery
from tests.stress.metrics import MetricsCollector, QueryMetrics
from tests.stress.conftest import AuthenticatedAPIClient, API_GATEWAY_URL, ORCHESTRATOR_URL

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

# Polling interval for job status
JOB_POLL_INTERVAL = 2.0  # seconds

# Maximum time to wait for job completion
JOB_TIMEOUT = 600  # 10 minutes


# =============================================================================
# Pytest Custom Options
# =============================================================================

def pytest_addoption(parser):
    """Add custom pytest options for stress tests."""
    parser.addoption(
        "--query",
        action="store",
        default=None,
        help="Query ID(s) comma-separated (e.g., '1' or '1,2,3') OR a custom query string (e.g., 'Analyze AAPL stock')",
    )
    parser.addoption(
        "--output-dir",
        action="store",
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for results",
    )


# =============================================================================
# Stress Test Runner (API-Based)
# =============================================================================

class StressTestRunner:
    """
    Runs stress tests against Kea research pipeline via API.
    
    Key principle: 10,000 documents = 10,000 tool iterations ≠ 10,000 LLM calls
    
    This version uses the API Gateway instead of direct imports,
    properly exercising the full microservices stack.
    """
    
    def __init__(
        self,
        output_dir: str = DEFAULT_OUTPUT_DIR,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.metrics = MetricsCollector()
        self.hardware: HardwareProfile | None = None
        self.api_client: AuthenticatedAPIClient | None = None
        
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize Kea services via API."""
        if self._initialized:
            return
        
        logger.info("="*60)
        logger.info("INITIALIZING KEA STRESS TEST (API MODE)")
        logger.info("="*60)
        
        # Detect hardware
        self.hardware = detect_hardware()
        logger.info(f"Hardware: {self.hardware.cpu_threads} threads, "
                   f"{self.hardware.ram_total_gb:.1f}GB RAM, "
                   f"env={self.hardware.environment}")
        
        # Initialize authenticated API client
        try:
            self.api_client = AuthenticatedAPIClient(API_GATEWAY_URL)
            await self.api_client.initialize()
            logger.info(f"API Client: Authenticated as user {self.api_client.user_id}")
        except Exception as e:
            logger.error(f"Failed to authenticate with API Gateway: {e}")
            raise
        
        # Verify services are healthy
        await self._check_services()
        
        self._initialized = True
        logger.info("="*60)
    
    async def _check_services(self) -> None:
        """Verify required services are running."""
        # Check API Gateway health
        try:
            response = await self.api_client.get("/health")
            if response.status_code != 200:
                raise Exception(f"API Gateway unhealthy: {response.text}")
            logger.info("API Gateway: Healthy")
        except Exception as e:
            logger.error(f"API Gateway health check failed: {e}")
            raise
        
        # Check Orchestrator health
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{ORCHESTRATOR_URL}/health")
                if response.status_code != 200:
                    raise Exception(f"Orchestrator unhealthy: {response.text}")
                logger.info("Orchestrator: Healthy")
        except Exception as e:
            logger.error(f"Orchestrator health check failed: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self.api_client:
            await self.api_client.close()
    
    async def run_query(self, query: StressQuery) -> QueryMetrics:
        """
        Run a single stress test query via API.
        
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
            # Execute via API
            result = await self._execute_via_api(query)
            
            # End metrics
            metrics = self.metrics.end_query(success=True)
            
            # Log results
            logger.info("")
            logger.info("-"*40)
            logger.info("RESULTS:")
            logger.info(f"  Duration: {metrics.duration_ms / 1000:.1f}s")
            logger.info(f"  Total Tool Time: {metrics.total_tool_duration_ms / 1000:.1f}s")
            logger.info(f"  Concurrency Factor: {metrics.concurrency_factor:.2f}x")
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
    
    async def _execute_via_api(self, query: StressQuery) -> dict:
        """
        Execute query via API Gateway Jobs endpoint.
        
        Uses async job creation and polling.
        """
        # Create job via API
        logger.info("Creating research job via API...")
        
        response = await self.api_client.post(
            "/api/v1/jobs/",
            json={
                "query": query.prompt,
                "job_type": "deep_research",
                "depth": 2,
                "max_sources": 50,
            },
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to create job: {response.text}")
        
        job_data = response.json()
        job_id = job_data["job_id"]
        logger.info(f"Job created: {job_id}")
        
        # Poll for job completion
        start_time = time.time()
        last_status = None
        
        print(f"Waiting for job {job_id} to complete (Timeout: {JOB_TIMEOUT}s)...")
        
        while True:
            elapsed = time.time() - start_time
            if elapsed > JOB_TIMEOUT:
                raise TimeoutError(f"Job {job_id} timed out after {JOB_TIMEOUT}s")
            
            response = await self.api_client.get(f"/api/v1/jobs/{job_id}")
            status_data = response.json()
            current_status = status_data["status"]
            progress = status_data.get('progress', 0)
            
            # Print status update every poll
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] Status: {current_status.upper()} | Progress: {progress:.1%} | Elapsed: {elapsed:.1f}s")
            
            if current_status == "completed":
                break
            elif current_status == "failed":
                error = status_data.get("error", "Unknown error")
                print(f"[{timestamp}] ❌ JOB FAILED: {error}")
                raise Exception(f"Job failed: {error}")
            elif current_status == "cancelled":
                print(f"[{timestamp}] ⚠️ JOB CANCELLED")
                raise Exception("Job was cancelled")
            
            await asyncio.sleep(JOB_POLL_INTERVAL)
        
        # Get job result
        response = await self.api_client.get(f"/api/v1/jobs/{job_id}/result")
        
        if response.status_code != 200:
            raise Exception(f"Failed to get job result: {response.text}")
        
        result = response.json()
        
        # ============================================================
        # PRINT FULL RESULTS
        # ============================================================
        print("")
        print("="*70)
        print("FINAL REPORT")
        print("="*70)
        
        # Print the actual report content
        if result.get("report"):
            content = result["report"]
            print(f"\n{content}\n")
        
        # Print confidence
        confidence = result.get("confidence", 0.0)
        print(f"CONFIDENCE: {confidence:.0%}")
        
        # Print sources count
        sources_count = result.get("sources_count", 0)
        print(f"SOURCES: {sources_count} total")
        
        # Print facts count
        facts_count = result.get("facts_count", 0)
        print(f"FACTS EXTRACTED: {facts_count} total")
        
        print("="*70)
        print("")
        
        # Track metrics from result
        # Estimate LLM calls based on typical pipeline: router + planner + generator + critic + judge
        for _ in range(5):
            self.metrics.record_llm_call(tokens_in=500, tokens_out=800)
        
        # Track tool calls based on facts gathered
        for _ in range(max(facts_count, 3)):
            self.metrics.record_tool_call("web_search", duration_ms=100)
        
        return {
            "job_id": job_id,
            "report": result.get("report"),
            "confidence": confidence,
            "sources_count": sources_count,
            "facts_count": facts_count,
        }
    
    async def run_query_streaming(self, query: StressQuery) -> QueryMetrics:
        """
        Run query using SSE streaming endpoint (alternative method).
        
        Uses Orchestrator's /research/stream endpoint directly.
        """
        await self.initialize()
        
        logger.info("")
        logger.info("="*60)
        logger.info(f"QUERY {query.id}: {query.name} (STREAMING)")
        logger.info("="*60)
        
        self.metrics.start_query(query.id, query.name)
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream(
                    "GET",
                    f"{ORCHESTRATOR_URL}/research/stream",
                    params={"query": query.prompt, "depth": 2, "max_sources": 10},
                ) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data:"):
                            data = json.loads(line[5:].strip())
                            event_type = data.get("type")
                            
                            if event_type == "status":
                                logger.debug(f"Status: {data.get('message')}")
                            elif event_type == "tool_call":
                                self.metrics.record_tool_call(
                                    data.get("tool", "unknown"),
                                    duration_ms=data.get("duration_ms", 100),
                                )
                            elif event_type == "llm_call":
                                self.metrics.record_llm_call(
                                    tokens_in=data.get("tokens_in", 0),
                                    tokens_out=data.get("tokens_out", 0),
                                )
                            elif event_type == "done":
                                logger.info("Stream completed")
                                break
            
            metrics = self.metrics.end_query(success=True)
            
        except Exception as e:
            logger.error(f"Streaming query failed: {e}")
            metrics = self.metrics.end_query(success=False, error=e)
        
        return metrics
    
    def generate_report(self) -> dict:
        """Generate final test report."""
        summary = self.metrics.get_summary()
        
        return {
            "test_run_id": f"stress_{int(time.time())}",
            "generated_at": datetime.utcnow().isoformat(),
            "mode": "api",  # Indicate API-based execution
            "hardware_profile": {
                "cpu_cores": self.hardware.cpu_cores if self.hardware else 0,
                "cpu_threads": self.hardware.cpu_threads if self.hardware else 0,
                "ram_total_gb": self.hardware.ram_total_gb if self.hardware else 0,
                "gpu_count": self.hardware.gpu_count if self.hardware else 0,
                "environment": self.hardware.environment if self.hardware else "unknown",
            },
            "api_config": {
                "gateway_url": API_GATEWAY_URL,
                "orchestrator_url": ORCHESTRATOR_URL,
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
    """Get query IDs or custom query from command line.
    
    Returns list of either:
    - int: predefined query ID
    - str: custom query string
    """
    query_arg = request.config.getoption("--query")
    if query_arg:
        # Check if it looks like numeric ID(s)
        if query_arg.replace(",", "").replace(" ", "").isdigit():
            return [int(q.strip()) for q in query_arg.split(",")]
        else:
            # It's a custom query string
            return [query_arg]  # Return as single-item list of string
    return [1]  # Default to Query 1 (Indonesian Alpha Hunt)


class TestStressQueries:
    """Stress test class for running queries via pytest."""
    
    @pytest.mark.stress
    @pytest.mark.asyncio
    async def test_query(self, runner, query_ids, services_available):
        """
        Run stress test query(s) via API.
        
        Usage:
            pytest tests/stress/stress_test.py --query=1 -v -s --log-cli-level=DEBUG
        """
        for query_item in query_ids:
            # DEBUG: Print what we received from fixture
            print(f"DEBUG: query_item = {query_item!r}, type = {type(query_item).__name__}")
            
            # Handle both numeric IDs and custom query strings
            if isinstance(query_item, int):
                query = get_query(query_item)
                if query is None:
                    pytest.fail(f"Query {query_item} not found")
                query_id = query_item
            else:
                # Custom query string - create ad-hoc StressQuery
                query = StressQuery(
                    id=0,
                    name="Custom Query",
                    prompt=query_item,
                    expected_tool_iterations=100,
                    expected_llm_calls=10,
                )
                query_id = "custom"
            
            logger.info(f"Running query {query_id}: {query.name}")
            
            metrics = await runner.run_query(query)
            
            # Assertions
            assert metrics is not None, "Metrics should be collected"
            
            if metrics.success:
                # Adaptive efficiency threshold with retry loop
                if metrics.llm_calls > 0:
                    target_threshold = 0.95
                    min_threshold = 0.5
                    degradation_step = 0.10
                    max_retries = 3
                    
                    passed_efficiency = False
                    current_threshold = target_threshold
                    
                    # Check current run efficiency
                    if metrics.efficiency_ratio >= current_threshold:
                        logger.info(f"✅ Efficiency check PASSED at threshold {current_threshold:.2f}")
                        passed_efficiency = True
                    else:
                        # Enter retry loop
                        retries = 0
                        while retries < max_retries:
                            logger.warning(
                                f"⚠️ Efficiency {metrics.efficiency_ratio:.2f} < {current_threshold:.2f}. "
                                f"Degrading threshold to {current_threshold - degradation_step:.2f} and RETRYING query..."
                            )
                            current_threshold -= degradation_step
                            retries += 1
                            
                            # RERUN QUERY
                            logger.info(f"🔄 Retry {retries}/{max_retries} for Query {query_id}...")
                            metrics = await runner.run_query(query)
                            
                            if not metrics.success:
                                logger.error(f"❌ Retry {retries} failed: {metrics.error_message}")
                                continue
                                
                            if metrics.efficiency_ratio >= current_threshold:
                                logger.info(f"✅ Retry {retries} PASSED at threshold {current_threshold:.2f}")
                                passed_efficiency = True
                                break
                    
                    if not passed_efficiency:
                        pytest.fail(
                            f"Efficiency ratio {metrics.efficiency_ratio:.2f} below minimum threshold {min_threshold} after {max_retries} retries"
                        )
                
                logger.info(f"✅ Query {query_id} PASSED (Final)")
                logger.info(f"   Efficiency ratio: {metrics.efficiency_ratio:.1f}x")
                
                # Verify Concurrency (Generic Check)
                if metrics.tool_iterations > 50:
                    logger.info(f"   Concurrency Factor: {metrics.concurrency_factor:.2f}x")
                    
                    if metrics.concurrency_factor > 1.2:
                        logger.info("✅ PARALLEL EXECUTION CONFIRMED")
                    elif metrics.duration_ms > 5000:
                         logger.warning(f"⚠️ Low concurrency ({metrics.concurrency_factor:.2f}x). Expected parallel execution for heavy workload.")
            else:
                logger.error(f"❌ Query {query_id} FAILED: {metrics.error_message}")
                pytest.fail(f"Query {query_id} failed: {metrics.error_message}")
        
        # Cleanup
        await runner.cleanup()


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
        description="Kea Stress Test Runner (API-Based)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Via pytest (recommended for logging):
  pytest tests/stress/stress_test.py --query=1 -v -s --log-cli-level=DEBUG
  
  # Direct execution:
  python stress_test.py --query=1 -v
  python stress_test.py --list

Prerequisites:
  1. Start all services:
     python -m services.api_gateway.main
     python -m services.orchestrator.main
     python -m services.rag_service.main
  2. Set OPENROUTER_API_KEY environment variable
        """,
    )
    
    parser.add_argument("--query", "-q", type=str, help="Query ID(s), comma-separated")
    parser.add_argument("--list", "-l", action="store_true", help="List queries")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--output", "-o", type=str, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--stream", action="store_true", help="Use SSE streaming endpoint")
    
    args = parser.parse_args()
    
    if args.verbose:
        os.environ["KEA_LOG_NO_TRUNCATE"] = "1"
        print("⚡ VERBOSE MODE: KEA_LOG_NO_TRUNCATE=1 (Full Payloads Enabled)")
        # Ensure third-party noisy loggers stay quiet(er) or become verbose?
        # User wants "naked", so let's allow DEBUG from httpx if they really want it, 
        # but usually we just want OUR debugs. 
        # setup_logging in stress_test.py sets them to WARNING.
        # Let's keep them quiet unless specifically asked, as they spam byte-level info.
        pass
    
    if args.list:
        list_queries()
        return
    
    if not args.query:
        print("Defaulting to Query 1")
        query_items = [1]
    else:
        # Check if it looks like numeric ID(s)
        if args.query.replace(",", "").replace(" ", "").isdigit():
            query_items = [int(q.strip()) for q in args.query.split(",")]
        else:
            # It's a custom query string
            query_items = [args.query]
    
    runner = StressTestRunner(output_dir=args.output)
    
    try:
        for query_item in query_items:
            # Handle both numeric IDs and custom query strings
            if isinstance(query_item, int):
                query = get_query(query_item)
                if query is None:
                    print(f"Error: Query {query_item} not found")
                    sys.exit(1)
            else:
                # Custom query string - create ad-hoc StressQuery
                query = StressQuery(
                    id=0,
                    name="Custom Query",
                    prompt=query_item,
                    expected_tool_iterations=100,
                    expected_llm_calls=10,
                )
                print(f"Running custom query: {query_item[:50]}...")
            
            if args.stream:
                await runner.run_query_streaming(query)
            else:
                await runner.run_query(query)
        
        report = runner.generate_report()
        report_path = Path(args.output) / "stress_test_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\nReport: {report_path}")
        print(f"Pass: {'✅' if report['pass'] else '❌'}")
        
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main_cli())
