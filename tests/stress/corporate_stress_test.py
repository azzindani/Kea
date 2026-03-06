#!/usr/bin/env python3
"""
Corporate Kernel Stress Test

Expectations on Final Output:
    This stress test evaluates how the high-level Tier 8 (Corporate Ops) and 
    Tier 9 (Corporate Gateway) handle massive swarms and system-wide orchestration.
    
    1. Gateway Stress (Tier 9):
       Classifies and strategizes a massive request, simulating the front door 
       of the Kea Corporation under heavy, complex load.
       
    2. Swarm Orchestration Stress (Tier 8):
       Forces the Team Orchestrator to build Sprint DAGs for hundreds of mission chunks.
       
    3. Workforce Allocation Stress (Tier 8):
       Forces the Workforce Manager to instantaneously match hundreds of specialist 
       profiles against simulated sub-objectives, testing the vector embedding and 
       pattern matching scale limits.
       
    4. Synthesis & Audit Stress (Tiers 8 & 9):
       Simulates the generation of hundreds of artifacts, forcing the Quality Resolver 
       and Gateway Synthesizer to process and merge immense amounts of context without crashing.

Usage:
    # Run via pytest
    python -m pytest tests/stress/corporate_stress_test.py -v -s --log-cli-level=DEBUG
    
    # Direct execution
    python tests/stress/corporate_stress_test.py
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path
from typing import Any

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.logging.main import get_logger
from kernel.corporate_gateway.engine import assess_strategy, synthesize_response
from kernel.corporate_gateway.types import ScalingMode
from kernel.team_orchestrator.engine import plan_sprints
from kernel.workforce_manager.engine import match_specialist
from kernel.workforce_manager.types import MissionChunk
from kernel.quality_resolver.engine import score_sprint_quality

logger = get_logger(__name__)

# Single massive query designed to trigger Swarm mode
DEFAULT_SWARM_QUERY = """
Build a comprehensive distributed supercomputer simulator, including frontend, backend, 
database sharding mechanisms, kubernetes deployment scripts, CI/CD pipelines, financial 
forecasting models for cloud costs, an intelligent AI load balancer, marketing materials, 
and a legal compliance framework for GDPR.
"""

import os

@pytest.fixture
def swarm_size():
    """Get swarm size from environment variable."""
    return int(os.environ.get("SWARM_SIZE", "100"))


@pytest.mark.stress
@pytest.mark.asyncio
async def test_corporate_kernel_stress(inference_kit, swarm_size):
    """
    Stress test for the Tier 8/9 Corporate Kernel.
    """
    query = DEFAULT_SWARM_QUERY
    logger.info("="*80)
    logger.info(f"🚀 INITIALIZING CORPORATE KERNEL STRESS TEST (TARGET SWARM SIZE: {swarm_size})")
    logger.info("="*80)
    
    total_start_time = time.time()
    
    # ------------------------------------------------------------------
    # PHASE 1: GATEWAY STRATEGY (TIER 9)
    # ------------------------------------------------------------------
    logger.info("\n[PHASE 1] Gateway Strategic Assessment")
    p1_start = time.time()
    
    strategy = await assess_strategy(request_content=query, session=None, kit=inference_kit)
    
    p1_dur = time.time() - p1_start
    if not hasattr(strategy, "scaling_mode"):
        logger.warning(f"Strategy assess_strategy did not return a StrategyAssessment: {strategy}")
    else:
        logger.info(f"   => Complexity: {strategy.complexity}")
        logger.info(f"   => Scaling Mode: {strategy.scaling_mode.value.upper()}")
        logger.info(f"   => Est. Agents: {strategy.estimated_agents}")
        logger.info(f"   => Phase Duration: {p1_dur:.3f}s")
    
    # ------------------------------------------------------------------
    # PHASE 2: TEAM ORCHESTRATOR - MASSIVE DAG (TIER 8)
    # ------------------------------------------------------------------
    logger.info(f"\n[PHASE 2] Ops Orchestrator: Generating {swarm_size} Mission Chunks")
    p2_start = time.time()
    
    # Synthetically generate massive chunk load
    chunks = []
    for i in range(swarm_size):
        chunks.append(
            MissionChunk(
                chunk_id=f"chk_{i}", 
                parent_objective_id="msg_stress_test", 
                domain="engineering" if i % 2 == 0 else "analysis", 
                sub_objective=f"Develop critical module {i}",
                depends_on=[f"chk_{i-1}"] if i > 0 and i % 5 != 0 else [] # Occasional parallelism
            )
        )
        
    plan_result = await plan_sprints(chunks, mission_id="stress_mission_1", kit=inference_kit)
    assert plan_result.is_success, "Orchestrator failed to build DAG."
    sprints = plan_result.signals[0].body["data"]["sprints"]
    
    p2_dur = time.time() - p2_start
    logger.info(f"   => Generated Sprints: {len(sprints)}")
    logger.info(f"   => Total Chunks Processed: {len(chunks)}")
    logger.info(f"   => Phase Duration: {p2_dur:.3f}s")
    
    # ------------------------------------------------------------------
    # PHASE 3: WORKFORCE MANAGER - PARALLEL HIRING (TIER 8)
    # ------------------------------------------------------------------
    logger.info(f"\n[PHASE 3] Ops Workforce: Parallel Specialist Matching ({swarm_size} agents)")
    p3_start = time.time()
    
    available_profiles = [
        {"profile_id": "prof-devops", "role_name": "DevOps Engineer", "skills": ["aws", "k8s", "docker", "engineering"]},
        {"profile_id": "prof-db", "role_name": "Database Admin", "skills": ["sql", "postgres", "engineering"]},
        {"profile_id": "prof-analyst", "role_name": "Data Analyst", "skills": ["analysis", "finance", "reports"]}
    ]
    
    # Run all matching concurrently
    match_tasks = []
    for chunk in chunks:
        match_tasks.append(match_specialist(chunk, available_profiles, kit=inference_kit))
    
    match_results = await asyncio.gather(*match_tasks)
    
    success_count = sum(1 for r in match_results if r.is_success)
    p3_dur = time.time() - p3_start
    
    logger.info(f"   => Specialists Successfully Matched: {success_count}/{swarm_size}")
    logger.info(f"   => Match Rate: {(success_count/swarm_size)*100:.1f}%")
    logger.info(f"   => Phase Duration: {p3_dur:.3f}s")
    
    # ------------------------------------------------------------------
    # PHASE 4: QUALITY RESOLVER & SYNTHESIS - MASSIVE AUDIT (TIER 8 & 9)
    # ------------------------------------------------------------------
    logger.info(f"\n[PHASE 4] Quality Audit & Executive Synthesis ({swarm_size} artifacts)")
    p4_start = time.time()
    
    mock_agent_results = []
    mock_artifacts = []
    for i in range(swarm_size):
        mock_agent_results.append({
            "agent_id": f"agent_{i}", 
            "quality_score": 0.85 + (i % 15) / 100.0, # Slight variation
            "confidence": 0.9, 
            "grounding_rate": 0.95
        })
        mock_artifacts.append({
            "content": f"Artifact payload from agent {i}. Completion status nominal.",
            "metadata": {"topic": "Stress Test Artifacts", "agent_id": f"agent_{i}"}
        })
        
    audit_result = await score_sprint_quality(mock_agent_results, sprint_id="stress_sprint_full", kit=inference_kit)
    assert audit_result.is_success
    audit_verdict = audit_result.signals[0].body["data"].get("overall", "fail")
    
    synth_result = await synthesize_response(
        artifacts=mock_artifacts,
        strategy=strategy if hasattr(strategy, "scaling_mode") else None,
        quality_report={"gaps": [], "completion_pct": 1.0, "quality_score": 0.9},
        kit=inference_kit
    )
    
    p4_dur = time.time() - p4_start
    
    logger.info(f"   => Audit Verdict: {audit_verdict.upper()}")
    if hasattr(synth_result, "sections"):
        logger.info(f"   => Synthesized Sections: {len(synth_result.sections)}")
        synth_preview = synth_result.executive_summary[:100] + "..." if synth_result.executive_summary else "N/A"
        logger.info(f"   => Synthesis Preview: {synth_preview}")
    logger.info(f"   => Phase Duration: {p4_dur:.3f}s")
    
    # ------------------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------------------
    total_dur = time.time() - total_start_time
    logger.info("")
    logger.info("="*80)
    logger.info("📊 CORPORATE KERNEL STRESS TEST METRICS")
    logger.info("="*80)
    logger.info(f"   [TOTAL TIME]   {total_dur:.3f}s")
    logger.info(f"   [SWARM SIZE]   {swarm_size} agents/chunks")
    logger.info(f"   [THROUGHPUT]   {swarm_size/total_dur:.1f} chunks/sec processed across corporate pipeline")
    logger.info("="*80)
    
    logger.info("✅ STRESS TEST PASSED SUCCESSFULLY")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Corporate Kernel Stress Test")
    parser.add_argument("--swarm-size", "-s", type=int, default=100, help="Number of concurrent chunks/agents")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args, unknown = parser.parse_known_args()
    
    pytest_args = ["-v", "-s", __file__]
    if args.verbose:
        pytest_args.append("--log-cli-level=DEBUG")
    else:
        pytest_args.append("--log-cli-level=INFO")
        
    os.environ["SWARM_SIZE"] = str(args.swarm_size)
    
    sys.exit(pytest.main(pytest_args))
