"""
Synthesis Worker.

Background worker for report synthesis.
"""

from __future__ import annotations

import asyncio
from typing import Any

from shared.config import get_settings
from shared.logging import setup_logging, get_logger, LogConfig
from shared.schemas import ResearchStatus


logger = get_logger(__name__)


class SynthesisWorker:
    """
    Worker for synthesizing research reports from facts.
    
    Takes collected facts and generates cohesive reports.
    """
    
    def __init__(self) -> None:
        self._running = False
    
    async def start(self) -> None:
        """Start the worker."""
        settings = get_settings()
        
        setup_logging(LogConfig(
            level=settings.log_level,
            format=settings.log_format,
            service_name="synthesis_worker",
        ))
        
        logger.info("Starting synthesis worker")
        self._running = True
        
        await self._run_loop()
    
    async def stop(self) -> None:
        """Stop the worker."""
        logger.info("Stopping synthesis worker")
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
        """Get next synthesis task from queue."""
        return None
    
    async def _process_task(self, task: dict) -> None:
        """Process a synthesis task."""
        job_id = task.get("job_id", "unknown")
        facts = task.get("facts", [])
        
        logger.info(f"Synthesizing report for {job_id} with {len(facts)} facts")
        
        try:
            report = await self._synthesize(facts, task.get("query", ""))
            
            await self._save_result(job_id, report)
            
        except Exception as e:
            logger.error(f"Synthesis failed for {job_id}: {e}")
    
    async def _synthesize(self, facts: list[dict], query: str) -> str:
        """Synthesize facts into a report."""
        import os
        import httpx
        
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        
        facts_text = "\n".join([
            f"- {f.get('entity', '')}: {f.get('attribute', '')} = {f.get('value', '')}"
            for f in facts[:50]
        ])
        
        prompt = f"""You are a research analyst. Synthesize the following facts into a coherent report.

Query: {query}

Facts:
{facts_text}

Create a well-structured report with:
1. Executive Summary
2. Key Findings
3. Data Analysis
4. Conclusions

Be concise but comprehensive. Include specific data points."""
        
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": "nvidia/nemotron-3-nano-30b-a3b:free",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 4000,
                    }
                )
                response.raise_for_status()
                data = response.json()
            
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"LLM synthesis failed: {e}")
            return f"# Report for: {query}\n\nFacts collected: {len(facts)}"
    
    async def _save_result(self, job_id: str, report: str) -> None:
        """Save synthesis result."""
        logger.info(f"Report saved for {job_id}")


async def main():
    """Run the synthesis worker."""
    worker = SynthesisWorker()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
