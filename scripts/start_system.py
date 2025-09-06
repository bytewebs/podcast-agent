#!/usr/bin/env python3
"""
System startup script to ensure Prefect is properly configured
"""
import asyncio
import subprocess
import time
import sys
import os
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def wait_for_prefect_server(max_retries=30):
    """Wait for Prefect server to be ready"""
    prefect_url = os.getenv('PREFECT_API_URL', 'http://localhost:4200')

    for i in range(max_retries):
        try:
            response = requests.get(f"{prefect_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Prefect server is ready!")
                return True
        except requests.exceptions.RequestException:
            pass

        print(f"⏳ Waiting for Prefect server... ({i+1}/{max_retries})")
        time.sleep(2)

    return False

async def deploy_and_start():
    """Deploy flows and start system"""
    print("🚀 Starting Podcast Generation System")

    # Wait for Prefect server
    if not wait_for_prefect_server():
        print("❌ Prefect server not available")
        return False

    # Deploy flows
    print("📦 Deploying Prefect flows...")
    try:
        from scripts.deploy_prefect_fixed import deploy_flows
        deployment_id = await deploy_flows()
        print(f"✅ Flows deployed successfully: {deployment_id}")
    except Exception as e:
        print(f"❌ Failed to deploy flows: {e}")
        return False

    # Start Prefect worker (if not already running)
    print("🔧 Starting Prefect worker...")
    try:
        # Check if worker is already running
        result = subprocess.run(
            ["prefect", "worker", "ls"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if "default-agent-pool" not in result.stdout:
            print("Starting new Prefect worker...")
            subprocess.Popen([
                "prefect", "worker", "start",
                "--pool", "default-agent-pool",
                "--name", "podcast-worker"
            ])
        else:
            print("✅ Prefect worker already running")

    except Exception as e:
        print(f"⚠️ Worker start failed: {e}")

    print("✅ System startup complete!")
    print("🌐 Prefect UI available at: http://localhost:4200")
    print("🌐 API available at: http://localhost:5050")

    return True

if __name__ == "__main__":
    success = asyncio.run(deploy_and_start())
    if not success:
        sys.exit(1)
