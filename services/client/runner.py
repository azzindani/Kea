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
    
    async def run_query(self, query: str) -> JobMetrics:
        """
        Run a single research query and return metrics.
        """
        job_id = str(uuid.uuid4())
        logger.info(f"🚀 Starting Research Job {job_id}: '{query}'")
        
        self.metrics.start_job(job_id, query)
        
        try:
            # 1. Submit Job
            # Note: We must adhere to the exact API expected by the orchestrator
            payload = {
                "query": query,
                "job_id": job_id,
                # Default configuration
                "depth": 3,
                "breadth": 3
            }
            
            response = await self.client.post("/api/v1/research/submit", json=payload)
            if response.status_code != 200:
                raise RuntimeError(f"Failed to submit job: {response.text}")
            
            # 2. Poll for Completion
            status = "running"
            while status in ["running", "pending", "queued"]:
                await asyncio.sleep(self.poll_interval)
                
                # Poll status endpoint
                # Assuming /api/v1/research/status/{job_id}
                status_resp = await self.client.get(f"/api/v1/research/status/{job_id}")
                if status_resp.status_code != 200:
                    logger.warning(f"Status check failed: {status_resp.status_code}")
                    continue
                
                data = status_resp.json()
                status = data.get("status", "unknown").lower()
                
                # Update metrics from server progress
                if "metrics" in data:
                    srv_metrics = data["metrics"]
                    # Sync tokens/tools if server provides them in real-time
                    # For now, we rely on final report or implicit tracking
                    pass
                
                logger.debug(f"Job {job_id} status: {status}")
            
            # 3. Retrieve Results
            if status == "completed":
                result_resp = await self.client.get(f"/api/v1/research/results/{job_id}")
                if result_resp.status_code == 200:
                   result_data = result_resp.json()
                   # Here we would parse final metrics if available
                   pass
                
                self.metrics.end_job(success=True)
                logger.info(f"✅ Job {job_id} Completed Successfully")
                
            else:
                error_msg = f"Job finished with status: {status}"
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
