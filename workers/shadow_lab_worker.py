"""
Shadow Lab Worker.

Background worker for hypothesis testing and simulations.
"""

from __future__ import annotations

import asyncio

from shared.config import get_settings
from shared.logging import LogConfig, get_logger, setup_logging

logger = get_logger(__name__)


class ShadowLabWorker:
    """
    Worker for running hypothesis tests and simulations.

    Features:
    - Code-based hypothesis testing
    - Data simulation
    - Statistical analysis
    """

    def __init__(self) -> None:
        self._running = False

    async def start(self) -> None:
        """Start the worker."""
        settings = get_settings()

        setup_logging(
            LogConfig(
                level=settings.log_level,
                format=settings.log_format,
                service_name="shadow_lab_worker",
            )
        )

        logger.info("Starting Shadow Lab worker")
        self._running = True

        await self._run_loop()

    async def stop(self) -> None:
        """Stop the worker."""
        logger.info("Stopping Shadow Lab worker")
        self._running = False

    async def _run_loop(self) -> None:
        """Main worker loop."""
        while self._running:
            try:
                task = await self._get_next_task()

                if task:
                    await self._process_task(task)
                else:
                    await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Worker error: {e}", exc_info=True)
                await asyncio.sleep(5)

    async def _get_next_task(self) -> dict | None:
        """Claim the next pending shadow_lab task from execution_batches."""
        try:
            from shared.dispatcher import get_dispatcher

            dispatcher = get_dispatcher()
            return await dispatcher.claim_next_task(batch_type="shadow_lab")
        except Exception as e:
            logger.warning(f"Shadow lab task poll failed: {e}")
            return None

    async def _process_task(self, task: dict) -> None:
        """Process a lab task."""
        task_id = task.get("task_id", str(task.get("batch_id", "unknown")))
        task_type = task.get("type", "hypothesis")

        logger.info(f"Processing lab task {task_id}: {task_type}")

        try:
            if task_type == "hypothesis":
                await self._test_hypothesis(task)
            elif task_type == "simulation":
                await self._run_simulation(task)
            elif task_type == "analysis":
                await self._run_analysis(task)
            else:
                await self._run_simulation(task)

            await self._mark_complete(task_id, "completed")
        except Exception as e:
            logger.error(f"Lab task {task_id} failed: {e}")
            await self._mark_complete(task_id, "failed")

    async def _mark_complete(self, task_id: str, status: str) -> None:
        """Update task status in execution_batches."""
        try:
            from shared.database.connection import get_database_pool

            pool = await get_database_pool()
            await pool.execute(
                "UPDATE execution_batches SET status = $1, updated_at = NOW() WHERE batch_id::text = $2",
                status,
                task_id,
            )
        except Exception as e:
            logger.warning(f"Failed to mark task {task_id} as {status}: {e}")

    async def _test_hypothesis(self, task: dict) -> None:
        """Test a hypothesis with code execution."""
        hypothesis = task.get("hypothesis", "")
        code = task.get("code", "")

        logger.info(f"Testing hypothesis: {hypothesis[:50]}...")

        try:
            from mcp_servers.python_server.tools.execute_code import execute_code_tool

            result = await execute_code_tool({"code": code, "timeout": 30})
            if result.isError:
                logger.error(f"Hypothesis test failed: {result.content[0].text}")
            else:
                logger.info("Hypothesis test completed")
        except Exception as e:
            logger.warning(f"Hypothesis execution failed (code runner unavailable): {e}")

    async def _run_simulation(self, task: dict) -> None:
        """Run a research simulation via the Orchestrator."""
        import os

        import httpx

        query = task.get("query") or task.get("hypothesis") or "Simulation task"
        orchestrator_url = os.getenv("ORCHESTRATOR_URL", "http://localhost:8001")

        logger.info(f"Firing simulation to orchestrator: {query[:80]}")
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                resp = await client.post(
                    f"{orchestrator_url}/research",
                    json={"query": query, "depth": task.get("depth", 2), "max_sources": 10},
                )
                resp.raise_for_status()
                logger.info(f"Simulation completed: {resp.json().get('job_id', 'unknown')}")
        except Exception as e:
            logger.warning(f"Simulation failed: {e}")

    async def _run_analysis(self, task: dict) -> None:
        """Run statistical analysis."""
        data = task.get("data", [])
        logger.info(f"Running analysis on {len(data)} data points")

        try:
            from mcp_servers.analysis_server.server import AnalysisServer

            server = AnalysisServer()
            await server._handle_meta_analysis({"data_points": data, "analysis_type": "comparison"})
            logger.info("Analysis completed")
        except Exception as e:
            logger.warning(f"Analysis server unavailable, skipping: {e}")


async def main():
    """Run the Shadow Lab worker."""
    worker = ShadowLabWorker()

    try:
        await worker.start()
    except KeyboardInterrupt:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
