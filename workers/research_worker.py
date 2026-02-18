"""
Research Worker.

Background worker for processing research jobs.
"""

from __future__ import annotations

import asyncio

from shared.config import get_settings
from shared.logging import LogConfig, get_logger, setup_logging
from shared.logging.metrics import ACTIVE_JOBS, JOBS_TOTAL
from shared.schemas import ResearchStatus

logger = get_logger(__name__)


class ResearchWorker:
    """
    Background worker for research jobs.

    Processes jobs from queue and executes the research graph.
    """

    def __init__(self) -> None:
        self._running = False
        self._current_job: str | None = None

    async def start(self) -> None:
        """Start the worker."""
        settings = get_settings()

        setup_logging(
            LogConfig(
                level=settings.log_level,
                format=settings.log_format,
                service_name="research_worker",
            )
        )

        logger.info("Starting research worker")
        self._running = True

        await self._run_loop()

    async def stop(self) -> None:
        """Stop the worker."""
        logger.info("Stopping research worker")
        self._running = False

    async def _run_loop(self) -> None:
        """Main worker loop."""
        while self._running:
            try:
                # Poll for jobs
                job = await self._get_next_job()

                if job:
                    await self._process_job(job)
                else:
                    # No job, wait before polling again
                    await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Worker error: {e}", exc_info=True)
                await asyncio.sleep(5)

    async def _get_next_job(self) -> dict | None:
        """Claim the next pending job from research_jobs via SELECT â€¦ FOR UPDATE SKIP LOCKED."""
        try:
            from shared.database.connection import get_database_pool

            pool = await get_database_pool()
            row = await pool.fetchrow(
                """
                UPDATE research_jobs
                SET status = 'running', updated_at = NOW()
                WHERE job_id = (
                    SELECT job_id FROM research_jobs
                    WHERE status = 'pending'
                    ORDER BY created_at ASC
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                RETURNING job_id, query, depth, max_sources, user_id
                """,
            )
            return dict(row) if row else None
        except Exception as e:
            logger.warning(f"Job queue poll failed: {e}")
            return None

    async def _process_job(self, job: dict) -> None:
        """Process a research job."""
        job_id = job.get("job_id", "unknown")

        logger.info(f"Processing job {job_id}")
        self._current_job = job_id

        ACTIVE_JOBS.labels(job_type="deep_research").inc()

        try:
            # Update status
            await self._update_job_status(job_id, ResearchStatus.RUNNING, 0.0)

            # Import and run the research graph
            from kernel.flow.graph import GraphState, compile_research_graph

            graph = compile_research_graph()

            initial_state: GraphState = {
                "job_id": job_id,
                "query": job.get("query", ""),
                "path": "",
                "status": ResearchStatus.RUNNING.value,
                "sub_queries": [],
                "hypotheses": [],
                "facts": [],
                "sources": [],
                "artifacts": [],
                "generator_output": "",
                "critic_feedback": "",
                "judge_verdict": "",
                "report": "",
                "confidence": 0.0,
                "iteration": 0,
                "max_iterations": job.get("depth", 3),
                "should_continue": True,
                "error": None,
            }

            # Execute graph
            final_state = await graph.ainvoke(initial_state)

            # Update job with result
            await self._update_job_status(
                job_id,
                ResearchStatus.COMPLETED,
                1.0,
                result={
                    "report": final_state.get("report"),
                    "confidence": final_state.get("confidence", 0.0),
                    "facts_count": len(final_state.get("facts", [])),
                    "sources_count": len(final_state.get("sources", [])),
                },
            )

            JOBS_TOTAL.labels(job_type="deep_research", status="success").inc()
            logger.info(f"Completed job {job_id}")

        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}", exc_info=True)

            await self._update_job_status(job_id, ResearchStatus.FAILED, 0.0, error=str(e))

            JOBS_TOTAL.labels(job_type="deep_research", status="error").inc()

        finally:
            ACTIVE_JOBS.labels(job_type="deep_research").dec()
            self._current_job = None

    async def _update_job_status(
        self,
        job_id: str,
        status: ResearchStatus,
        progress: float,
        result: dict | None = None,
        error: str | None = None,
    ) -> None:
        """Update job status in the research_jobs table."""
        try:
            import json

            from shared.database.connection import get_database_pool

            pool = await get_database_pool()
            await pool.execute(
                """
                UPDATE research_jobs
                SET status = $1,
                    progress = $2,
                    result = $3,
                    error_message = $4,
                    updated_at = NOW(),
                    completed_at = CASE WHEN $1 IN ('completed', 'failed') THEN NOW() ELSE completed_at END
                WHERE job_id = $5
                """,
                status.value,
                progress,
                json.dumps(result) if result else None,
                error,
                job_id,
            )
        except Exception as e:
            logger.warning(f"Failed to update job {job_id} status: {e}")
        logger.debug(
            f"Job {job_id} status: {status.value}",
            extra={"progress": progress, "error": error},
        )


async def main():
    """Run the research worker."""
    worker = ResearchWorker()

    try:
        await worker.start()
    except KeyboardInterrupt:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
