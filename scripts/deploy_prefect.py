#!/usr/bin/env python3
"""
Fixed Prefect deployment script for Prefect 2.14
"""
import asyncio
import os
import sys
import time
import traceback

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def deploy_flows():
    """Deploy Prefect flows with proper configuration"""

    try:
        # Wait for server to be fully ready
        print("Waiting for Prefect server to be fully ready...")
        time.sleep(30)

        from prefect import get_client
        from prefect.deployments import Deployment
        from orchestration.flows.podcast_generation_flow import podcast_generation_flow

        async with get_client() as client:
            # Check server connection
            try:
                server_info = await client.api_healthcheck()
                print(f"✅ Connected to Prefect server")
            except Exception as e:
                print(f"⚠️ Server health check failed: {e}")

            # Delete existing work pool if it exists (to recreate with correct type)
            try:
                work_pools = await client.read_work_pools()
                for pool in work_pools:
                    if pool.name == "default-agent-pool":
                        print(f"Deleting existing work pool: {pool.name} (type: {pool.type})")
                        await client.delete_work_pool(pool.name)
                        break
            except Exception as e:
                print(f"⚠️ Work pool deletion failed: {e}")

            # Create work pool with correct type
            try:
                print("Creating new work pool with 'process' type...")
                await client.create_work_pool(
                    work_pool={
                        "name": "default-agent-pool",
                        "type": "process",
                        "description": "Process work pool for podcast generation"
                    }
                )
                print("✅ Work pool created successfully")
            except Exception as e:
                print(f"⚠️ Work pool creation failed: {e}")

            # Create deployment using the correct async approach
            try:
                print("Creating deployment...")

                # Build deployment
                deployment = await Deployment.build_from_flow(
                    flow=podcast_generation_flow,
                    name="podcast-generation-deployment",
                    description="AI Podcast Generation Pipeline",
                    tags=["podcast", "ai", "generation"],
                    work_pool_name="default-agent-pool",
                    schedule=None,
                    parameters={}
                )

                # Apply deployment
                deployment_id = await deployment.apply()
                print(f"✅ Deployment created with ID: {deployment_id}")

                return deployment_id
            except Exception as e:
                print(f"❌ Deployment creation failed: {e}")
                traceback.print_exc()
                return None

    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    try:
        result = asyncio.run(deploy_flows())
        if result:
            print("✅ Deployment successful")
            sys.exit(0)
        else:
            print("⚠️ Deployment failed but continuing...")
            sys.exit(0)  # Don't fail the container
    except Exception as e:
        print(f"❌ Script failed: {e}")
        sys.exit(0)  # Don't fail the container

