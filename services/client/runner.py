"""
Research Job Runner.

Handles job submission, polling, and result management.
"""

import asyncio
import json
import uuid
from typing import Any, Dict, Optional

from shared.logging import get_logger
from services.client.api import ResearchClient
from services.client.metrics import MetricsCollector, JobMetrics

logger = get_logger(__name__)


class ResearchRunner:
    """
    Executes research jobs and tracks their progress.
    """
    
    def __init__(self, api_client: ResearchClient, metrics: MetricsCollector):
        self.client = api_client
        self.metrics = metrics
        self.poll_interval = 2.0  # Seconds
    
    async def run_query(
        self, 
        query: str,
        seed_facts: list[dict] | None = None,
        error_feedback: list[dict] | None = None,
    ) -> JobMetrics:
        """
        Run a single research query and return metrics.
        
        Args:
            query: The research query to run
            seed_facts: Optional facts from previous attempt to build upon
            error_feedback: Optional errors from previous attempt to learn from
        """
        job_id = str(uuid.uuid4())
        seed_count = len(seed_facts) if seed_facts else 0
        error_count = len(error_feedback) if error_feedback else 0
        logger.info(f"🚀 Starting Research Job {job_id}: '{query}' (seed_facts={seed_count}, errors={error_count})")
        
        self.metrics.start_job(job_id, query)
        
        try:
            # 1. Submit Job
            # Note: We must adhere to the exact API expected by the orchestrator
            # API Gateway routes jobs to /api/v1/jobs
            payload = {
                "query": query,
                "job_type": "deep_research", # Required by API Gateway
                "depth": 2,
                "max_sources": 50,
            }
            
            # Add seed context if provided (for cross-attempt sharing)
            if seed_facts:
                payload["seed_facts"] = seed_facts
            if error_feedback:
                payload["error_feedback"] = error_feedback
            
            response = await self.client.post("/api/v1/jobs/", json=payload)
            if response.status_code != 200:
                raise RuntimeError(f"Failed to submit job: {response.text}")
            
            job_data = response.json()
            # Ensure we use the ID returned by server if different
            server_job_id = job_data.get("job_id")
            if server_job_id:
                job_id = server_job_id
                # Update metrics with real ID
                self.metrics._current_job.job_id = job_id

            logger.info(f"Job submitted successfully. Server ID: {job_id}")
            
            # 2. Poll for Completion with retry on network errors
            status = "running"
            poll_errors = 0
            max_poll_errors = 5  # Allow up to 5 consecutive network errors
            
            while status in ["running", "pending", "queued"]:
                await asyncio.sleep(self.poll_interval)
                
                try:
                    # Poll status endpoint
                    status_resp = await self.client.get(f"/api/v1/jobs/{job_id}")
                    poll_errors = 0  # Reset on success
                    
                    if status_resp.status_code != 200:
                        logger.warning(f"Status check failed: {status_resp.status_code}")
                        continue
                    
                    data = status_resp.json()
                    status = data.get("status", "unknown").lower()
                    
                    # Update metrics from server progress
                    if "metrics" in data:
                        srv_metrics = data["metrics"]
                        # Sync tokens/tools if server provides them in real-time
                        pass
                    
                    logger.debug(f"Job {job_id} status: {status}")
                    
                except Exception as poll_err:
                    poll_errors += 1
                    logger.warning(f"Poll error {poll_errors}/{max_poll_errors}: {type(poll_err).__name__}: {poll_err}")
                    
                    if poll_errors >= max_poll_errors:
                        logger.error(f"Max poll errors reached, giving up on job {job_id}")
                        raise
                    
                    # Wait longer before retrying after error
                    await asyncio.sleep(self.poll_interval * 2)
            
            # 3. Retrieve Results
            if status == "completed":
                result_resp = await self.client.get(f"/api/v1/jobs/{job_id}/result")
                if result_resp.status_code == 200:
                   result_data = result_resp.json()
                   
                   # Store the report
                   self.metrics._current_job.report = result_data.get("report")
                   
                   # API returns these at top level (not nested in metrics)
                   # JobResult schema: job_id, status, report, confidence, facts_count, sources_count, facts, errors
                   self.metrics._current_job.confidence = result_data.get("confidence", 0.0)
                   self.metrics._current_job.facts_count = result_data.get("facts_count", 0)
                   self.metrics._current_job.sources_count = result_data.get("sources_count", 0)
                   
                   # Store facts and errors for cross-attempt context sharing
                   self.metrics._current_job.facts = result_data.get("facts", [])
                   self.metrics._current_job.errors = result_data.get("errors", [])
                   
                   logger.info(f"Result received: confidence={result_data.get('confidence')}, facts={result_data.get('facts_count')}, sources={result_data.get('sources_count')}")
                
                self.metrics.end_job(success=True)
                logger.info(f"✅ Job {job_id} Completed Successfully")
                
            else:
                error_msg = f"Job finished with status: {status}"
                # Try to get error details
                if status == "failed":
                     status_resp = await self.client.get(f"/api/v1/jobs/{job_id}")
                     if status_resp.status_code == 200:
                         error_msg = status_resp.json().get("error", error_msg)
                
                self.metrics.end_job(success=False, error=error_msg)
                logger.error(f"❌ Job {job_id} Failed: {error_msg}")

        except Exception as e:
            logger.exception(f"Error running job {job_id}")
            self.metrics.end_job(success=False, error=str(e))
            
        return self.metrics._all_jobs[-1]
    
    async def cleanup(self):
        """Cleanup resources."""
        # Optional: Cancel pending jobs
        pass
