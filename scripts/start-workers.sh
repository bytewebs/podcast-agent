#!/bin/bash

echo "🚀 Starting all podcast generation workers..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Function to start worker in background
start_worker() {
    local worker_name=$1
    local worker_script=$2
    
    print_info "Starting ${worker_name}..."
    python3 "${worker_script}" &
    echo $! > "logs/${worker_name}.pid"
    print_status "${worker_name} started (PID: $!)"
}

# Create logs directory
mkdir -p logs

# Start all workers
start_worker "outline-worker" "workers/outline_worker.py"
start_worker "outline-evaluation-worker" "workers/outline_evaluation_worker.py"
start_worker "outline-guardrails-worker" "workers/outline_guardrails_worker.py"
start_worker "outline-approval-worker" "workers/outline_approval_worker.py"
start_worker "script-worker" "workers/script_worker.py"
start_worker "script-evaluation-worker" "workers/script_evaluation_worker.py"
start_worker "script-guardrails-worker" "workers/script_guardrails_worker.py"
start_worker "script-approval-worker" "workers/script_approval_worker.py"
start_worker "tts-worker" "workers/tts_worker.py"
start_worker "tts-evaluation-worker" "workers/tts_evaluation_worker.py"
start_worker "audio-approval-worker" "workers/audio_approval_worker.py"
start_worker "publishing-worker" "workers/publishing_worker.py"

echo ""
print_status "All workers started successfully!"
print_info "Worker PIDs saved in logs/ directory"
print_info "To stop workers: ./scripts/stop-workers.sh"
print_info "To view logs: tail -f logs/*.log"

# Wait for all background processes
echo ""
print_info "Workers running... Press Ctrl+C to stop all workers"
wait
