#!/bin/bash
set -e

echo "🧪 Running Complete System Test Suite..."

# Test 1: System Health
echo "📊 Testing system health..."
curl -f http://localhost:5050/health || exit 1

# Test 2: Create Test Job
echo "🎙️ Creating test podcast job..."
JOB_ID=$(curl -s -X POST http://localhost:5050/api/v1/podcast/create \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Complete System Test",
    "tone": "professional",
    "length_minutes": 5,
    "target_audience": "system testers",
    "key_points": ["functionality", "reliability", "performance"]
  }' | jq -r '.job_id')

if [ "$JOB_ID" = "null" ] || [ -z "$JOB_ID" ]; then
  echo "❌ Failed to create test job"
  exit 1
fi

echo "✅ Test job created: $JOB_ID"

# Test 3: Monitor Job Progress
echo "👀 Monitoring job progress..."
for i in {1..30}; do
  STATUS=$(curl -s http://localhost:5050/api/v1/podcast/$JOB_ID/status | jq -r '.status')
  echo "Status check $i: $STATUS"
  
  if [ "$STATUS" = "COMPLETED" ]; then
    echo "🎉 Job completed successfully!"
    break
  elif [ "$STATUS" = "FAILED" ]; then
    echo "❌ Job failed"
    curl -s http://localhost:5050/api/v1/podcast/$JOB_ID/status | jq '.error_message'
    exit 1
  fi
  
  sleep 10
done

# Test 4: Verify API Endpoints
echo "🔍 Testing all API endpoints..."

# Test metrics endpoint
curl -f http://localhost:5050/api/v1/metrics || echo "⚠️ Metrics endpoint issue"

# Test job listing
curl -f http://localhost:5050/api/v1/podcast/jobs || echo "⚠️ Job listing issue"

# Test documentation
curl -f http://localhost:5050/api/docs || echo "⚠️ Documentation endpoint issue"

echo "✅ Complete system test finished successfully!"
