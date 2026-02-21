#!/usr/bin/env python3
"""
Research CLI Tool.

Command-line interface for running research jobs.
Usage:
    python scripts/cli.py --query "Analyze BCA Bank" --env dev
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared.logging import setup_logging, LogConfig, LogLevel, get_logger
from services.client.api import ResearchClient
from services.client.runner import ResearchRunner
from services.client.metrics import MetricsCollector

logger = get_logger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Research CLI Tool")
    
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="Query to research (e.g., 'Analyze Apple')"
    )
    
    parser.add_argument(
        "--env",
        type=str,
        default="dev",
        choices=["dev", "prod", "local"],
        help="Environment to run against (default: dev)"
    )
    
    parser.add_argument(
        "--url",
        type=str,
        help="Custom API URL (overrides --env default)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()

def get_base_url(env: str, custom_url: str = None) -> str:
    if custom_url:
        return custom_url
        
    from shared.service_registry import ServiceRegistry, ServiceName
    
    if env == "prod":
        return "https://api.example.com" # Update when prod env exists
        
    return ServiceRegistry.get_url(ServiceName.GATEWAY)

async def main():
    args = parse_args()
    
    # Setup logging
    log_level = LogLevel.DEBUG if args.verbose else LogLevel.INFO
    setup_logging(LogConfig(level=log_level, format="console", service_name="cli"))
    
    base_url = get_base_url(args.env, args.url)
    
    logger.info(f"Starting research job against {base_url}")
    logger.info(f"Query: {args.query}")
    
    # Initialize components
    # In a real CLI, we might load credentials from a config file or env vars
    # For now, we use the defaults in ResearchClient which match dev/local
    client = ResearchClient(base_url=base_url)
    metrics = MetricsCollector()
    runner = ResearchRunner(client, metrics)
    
    try:
        await client.initialize()
        
        # Run the job
        job_metrics = await runner.run_query(args.query)
        
        if job_metrics.success:
            logger.info("✅ Job Completed Successfully")
            logger.info(f"Duration: {job_metrics.duration_ms}ms")
            logger.info(f"Efficiency: {job_metrics.efficiency_ratio:.2f}")
        else:
            logger.error(f"❌ Job Failed: {job_metrics.error}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Job cancelled by user")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
