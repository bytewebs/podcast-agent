#!/usr/bin/env python3
"""
Simple working Prefect deployment script
"""
import asyncio
import os
import sys
import time
import traceback

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def deploy_flows():
    """Deploy Prefect flows with simple approach"""

    try:
        print("Starting deployment process...")
        time.sleep(10)  # Wait for server

        from prefect import get_client
        from prefect.deployments import Deployment
        from orchestration.flows.podcast_generation_flow import podcast_generation_flow

        async with get_client() as client:
            print("✅ Connected to Prefect server")

            # Don't delete existing work pools - let the worker create them
            print("Skipping work pool management - letting worker handle it")

            # Create deployment with a work pool that will be created by the worker
            print("Creating deployment...")

            deployment = await Deployment.build_from_flow(
                flow=podcast_generation_flow,
                name="podcast-generation-deployment",
                description="AI Podcast Generation Pipeline",
                tags=["podcast", "ai", "generation"],
                work_pool_name="default-agent-pool",  # Worker will create this
                schedule=None,
                parameters={}
            )

            # Apply deployment
            deployment_id = await deployment.apply()
            print(f"✅ Deployment created with ID: {deployment_id}")

            return deployment_id

    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    try:
        result = asyncio.run(deploy_flows())
        if result:
            print("✅ Deployment successful")
        else:
            print("⚠️ Deployment failed")
        sys.exit(0)  # Always exit successfully to not break container
    except Exception as e:
        print(f"❌ Script failed: {e}")
        sys.exit(0)
