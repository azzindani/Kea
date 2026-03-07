#!/usr/bin/env python3
"""
Live Human Kernel Runner

This script executes the Tier 7 Human Kernel with REAL tool execution
enabled. It requires the Kea microservices stack (specifically MCP Host)
to be running.
"""

import asyncio
import sys
import time
from pathlib import Path
import httpx
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from kernel.conscious_observer.engine import ConsciousObserver
from kernel.lifecycle_controller.types import SpawnRequest
from kernel.modality.types import RawInput
from shared.config import get_settings
from shared.inference_kit import InferenceKit
from shared.logging.main import setup_logging, LogConfig, get_logger, LogLevel
from shared.service_registry import ServiceName, ServiceRegistry

# Initialize logging
setup_logging(LogConfig(
    level=LogLevel.INFO,
    format="console",
    service_name="live-kernel"
))

logger = get_logger(__name__)

async def real_tool_executor(tool_name: str, arguments: dict) -> dict:
    """HTTP bridge to the real MCP Host service."""
    settings = get_settings()
    mcp_url = ServiceRegistry.get_url(ServiceName.MCP_HOST)
    
    async with httpx.AsyncClient(timeout=settings.timeouts.tool_execution) as client:
        try:
            resp = await client.post(
                f"{mcp_url}/tools/execute",
                json={"tool_name": tool_name, "arguments": arguments},
            )
            if resp.status_code == 200:
                return resp.json()
            else:
                return {"error": f"Tool execution failed with status {resp.status_code}: {resp.text}"}
        except Exception as e:
            return {"error": f"Connection to MCP Host failed: {str(e)}"}

@pytest.mark.asyncio
async def test_run_live_kernel():
    query = "compare tech giant competition in US for cloud indstry, GCP, AWS, and Azure"
    
    logger.info("="*80)
    logger.info("🚀 INITIALIZING LIVE HUMAN KERNEL")
    logger.info(f"🎯 QUERY: {query}")
    logger.info("="*80)
    
    # 1. Setup Inference Kit with Real Tool Executor
    from shared.llm.openrouter import OpenRouterProvider
    from shared.llm.provider import LLMConfig
    
    settings = get_settings()
    llm = OpenRouterProvider()
    llm_config = LLMConfig(
        model=settings.llm.default_model,
        temperature=0.7,
        max_tokens=4096
    )
    
    kit = InferenceKit(
        llm=llm,
        llm_config=llm_config,
        tool_executor=real_tool_executor  # <--- THIS ENABLES REAL TOOLS
    )
    
    # 2. Instantiate the human kernel
    observer = ConsciousObserver(kit=kit)
    
    # 3. Process the query
    raw_input = RawInput(content=query)
    spawn_request = SpawnRequest(role="senior_cloud_analyst", objective=query)
    
    start_time = time.time()
    result = await observer.process(
        raw_input=raw_input,
        spawn_request=spawn_request
    )
    duration = time.time() - start_time
    
    # 4. Extract and print result
    if result.is_success:
        obs_res = result.signals[0].body.get("data", {}) or {}
        filtered_out = obs_res.get('filtered_output') or {}
        output_content = filtered_out.get('content', 'NO CONTENT')
        
        print("\n" + "="*80)
        print("🏆 FINAL LIVE ANALYSIS:")
        print("="*80)
        print(output_content)
        print("="*80)
        print(f"Done in {duration:.2f}s | Cycles: {obs_res.get('total_cycles', 0)}")
    else:
        logger.error(f"Kernel processing failed: {result.error}")


