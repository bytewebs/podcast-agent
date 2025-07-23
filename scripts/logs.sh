#!/bin/bash

# Colors
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

if [ -z "$1" ]; then
    print_info "Showing logs for all services..."
    docker-compose logs -f --tail=50
else
    print_info "Showing logs for $1..."
    docker-compose logs -f --tail=50 "$1"
fi