#!/bin/bash

echo "🧪 Testing podcast generation API..."

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

API_URL="http://localhost:5050"

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

test_endpoint() {
    local name=$1
    local url=$2
    local method=${3:-GET}
    local data=${4:-}
    
    print_info "Testing ${name}..."
    
    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$url" \
            -H "Content-Type: application/json" \
            -d "$data")
    else
        response=$(curl -s -w "\n%{http_code}" "$url")
    fi
    
    # Split response and status code
    body=$(echo "$response" | head -n -1)
    status=$(echo "$response" | tail -n1)
    
    if [[ "$status" == "2"* ]]; then
        print_success "${name} - Status: ${status}"
        return 0
    else
        print_error "${name} - Status: ${status}"
        echo "Response: $body"
        return 1
    fi
}

# Test 1: Health endpoint
test_endpoint "Health Check" "${API_URL}/health"

# Test 2: API Documentation
test_endpoint "API Documentation" "${API_URL}/api/docs"

# Test 3: List Jobs (empty initially)
test_endpoint "List Jobs" "${API_URL}/api/v1/podcast/jobs"

# Test 4: Create a test podcast
TEST_PAYLOAD='{
    "topic": "API Test Podcast",
    "tone": "professional",
    "length_minutes": 10,
    "target_audience": "developers",
    "key_points": ["testing", "validation", "quality assurance"],
    "voice_preference": "professional_female",
    "additional_context": "This is a test podcast created by the API test script"
}'

print_info "Creating test podcast job..."
create_response=$(curl -s -X POST "${API_URL}/api/v1/podcast/create" \
    -H "Content-Type: application/json" \
    -d "$TEST_PAYLOAD")

echo "Create response: $create_response"

# Extract job ID from response
JOB_ID=$(echo "$create_response" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('job_id', ''))" 2>/dev/null || echo "")

if [ -n "$JOB_ID" ] && [ "$JOB_ID" != "null" ]; then
    print_success "Test job created: $JOB_ID"
    
    # Test 5: Check job status
    test_endpoint "Job Status" "${API_URL}/api/v1/podcast/${JOB_ID}/status"
    
    # Test 6: List jobs again (should now have our test job)
    test_endpoint "List Jobs (with test job)" "${API_URL}/api/v1/podcast/jobs"
    
    # Test 7: Get system metrics
    test_endpoint "System Metrics" "${API_URL}/api/v1/metrics"
    
    print_info "Monitoring job progress for 30 seconds..."
    for i in {1..6}; do
        sleep 5
        status_response=$(curl -s "${API_URL}/api/v1/podcast/${JOB_ID}/status")
        status=$(echo "$status_response" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('status', 'unknown'))" 2>/dev/null || echo "unknown")
        print_info "Job status check $i: $status"
        
        if [ "$status" = "COMPLETED" ]; then
            print_success "Job completed successfully!"
            break
        elif [ "$status" = "FAILED" ]; then
            print_error "Job failed"
            break
        fi
    done
    
else
    print_error "Failed to create test job or extract job ID"
fi

# Test 8: Invalid requests
print_info "Testing invalid requests..."

# Invalid payload
curl -s -o /dev/null -w "Invalid payload test - Status: %{http_code}\n" \
    -X POST "${API_URL}/api/v1/podcast/create" \
    -H "Content-Type: application/json" \
    -d '{"invalid": "data"}'

# Missing required fields
curl -s -o /dev/null -w "Missing fields test - Status: %{http_code}\n" \
    -X POST "${API_URL}/api/v1/podcast/create" \
    -H "Content-Type: application/json" \
    -d '{"topic": "Test"}'

# Non-existent job status
curl -s -o /dev/null -w "Non-existent job test - Status: %{http_code}\n" \
    "${API_URL}/api/v1/podcast/fake_job_id/status"

echo ""
print_success "API testing completed!"
print_info "View detailed logs with: docker-compose logs api"
