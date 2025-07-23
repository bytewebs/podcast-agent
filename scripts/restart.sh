#!/bin/bash

echo "🔄 Restarting podcast generation system..."

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

# Stop services
print_info "Stopping services..."
docker-compose down

# Wait a moment
sleep 5

# Start services
print_info "Starting services..."
docker-compose up -d

# Wait for services to be ready
print_info "Waiting for services to be ready..."
sleep 30

# Check health
if curl -f http://localhost:5050/health &> /dev/null; then
    print_status "System restarted successfully!"
    print_info "API available at: http://localhost:5050"
else
    echo "⚠️ System may still be starting up. Check with: docker-compose ps"
fi