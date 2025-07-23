#!/bin/bash

echo "🛑 Stopping podcast generation system..."

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Stop all services
print_info "Stopping all Docker services..."
docker-compose down

# Stop individual worker processes if running
if [ -d "logs" ]; then
    for pidfile in logs/*.pid; do
        if [ -f "$pidfile" ]; then
            PID=$(cat "$pidfile")
            if kill -0 "$PID" 2>/dev/null; then
                kill "$PID"
                print_info "Stopped worker process: $PID"
            fi
            rm -f "$pidfile"
        fi
    done
fi

print_status "Podcast generation system stopped successfully!"
