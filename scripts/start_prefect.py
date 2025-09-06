#!/usr/bin/env python3
"""
Start Prefect services and deploy flows
"""

import asyncio
import subprocess
import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def wait_for_prefect_server():
    """Wait for Prefect server to be ready"""
    import requests
    
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:4200/api/health")
            if response.status_code == 200:
                print("Prefect server is ready!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        
        print(f"Waiting for Prefect server... ({i+1}/{max_retries})")
        time.sleep(2)
    
    return False

async def main():
    """Main startup function"""
    print("🚀 Starting Prefect-based Podcast Generation System")
    
    # Wait for Prefect server
    if not wait_for_prefect_server():
        print("❌ Prefect server not available")
        sys.exit(1)
    
    # Deploy flows
    print("📦 Deploying Prefect flows...")
    from scripts.deploy_prefect import deploy_flows
    
    try:
        deployment_id = await deploy_flows()
        print(f"✅ Flows deployed successfully: {deployment_id}")
    except Exception as e:
        print(f"❌ Failed to deploy flows: {e}")
        sys.exit(1)
    
    print("✅ Prefect system ready!")
    print("🌐 Prefect UI available at: http://localhost:4200")

if __name__ == "__main__":
    asyncio.run(main())
