
#!/bin/bash
set -e

echo "⚡ Running Load Test..."

# Create multiple jobs simultaneously
JOBS=()
for i in {1..5}; do
  echo "Creating job $i..."
  JOB_ID=$(curl -s -X POST http://localhost:5050/api/v1/podcast/create \
    -H "Content-Type: application/json" \
    -d "{
      \"topic\": \"Load Test Job $i\",
      \"tone\": \"professional\",
      \"length_minutes\": 3,
      \"target_audience\": \"load testers\"
    }" | jq -r '.job_id')
  
  JOBS+=($JOB_ID)
  echo "Created job: $JOB_ID"
done

echo "📊 Monitoring ${#JOBS[@]} jobs..."

# Monitor all jobs
COMPLETED=0
FAILED=0

for job in "${JOBS[@]}"; do
  for i in {1..60}; do
    STATUS=$(curl -s http://localhost:5050/api/v1/podcast/$job/status | jq -r '.status')
    
    if [ "$STATUS" = "COMPLETED" ]; then
      COMPLETED=$((COMPLETED + 1))
      echo "✅ Job $job completed"
      break
    elif [ "$STATUS" = "FAILED" ]; then
      FAILED=$((FAILED + 1))
      echo "❌ Job $job failed"
      break
    fi
    
    sleep 5
  done
done

echo "📈 Load test results:"
echo "   Completed: $COMPLETED"
echo "   Failed: $FAILED"
echo "   Success Rate: $(echo "scale=2; $COMPLETED * 100 / ${#JOBS[@]}" | bc)%"

if [ $COMPLETED -gt 0 ]; then
  echo "✅ Load test passed!"
else
  echo "❌ Load test failed!"
  exit 1
fi